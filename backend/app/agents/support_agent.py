from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import operator
import os


class AgentState(TypedDict):
    context: list[str]
    query: str
    creator_id: str
    response: str
    sources: list[str]
    should_escalate: bool


class SupportAgent:
    def __init__(self, vector_store_service):
        self.vector_store = vector_store_service
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("retrieve_context", self.retrieve_context)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("check_escalation", self.check_escalation)

        workflow.add_edge(START, "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("generate_response", "check_escalation")
        workflow.add_edge("check_escalation", END)

        return workflow.compile()

    async def retrieve_context(self, state: AgentState) -> AgentState:
        query = state["query"]
        creator_id = state["creator_id"]

        results = await self.vector_store.similarity_search(
            query=query,
            creator_id=creator_id,
            k=4
        )

        context = [doc.page_content for doc, score in results]
        sources = [
            f"{doc.metadata.get('source', 'Unknown')} (Score: {score:.2f})"
            for doc, score in results
        ]

        return {
            **state,
            "context": context,
            "sources": sources
        }

    async def generate_response(self, state: AgentState) -> AgentState:
        context_str = "\n\n".join(state["context"])
        query = state["query"]

        messages = [
            SystemMessage(content="""You are a helpful AI assistant for a creator's course or digital product.
            Your role is to answer student questions based on the course content provided.

            Guidelines:
            - Only answer based on the context provided
            - If the context doesn't contain relevant information, say you don't know
            - Cite specific sources when possible (e.g., "In Module 3...")
            - Be friendly and helpful in the creator's voice
            - If the question requires human intervention, flag it for escalation"""),
            HumanMessage(content=f"""Context from course materials:
            {context_str}

            Student question: {query}

            Please provide a helpful response based on the context above.""")
        ]

        response = await self.llm.ainvoke(messages)

        return {
            **state,
            "response": response.content
        }

    async def check_escalation(self, state: AgentState) -> AgentState:
        response_lower = state["response"].lower()

        escalation_triggers = [
            "i don't know",
            "not sure",
            "can't find",
            "unclear",
            "need more information"
        ]

        should_escalate = any(trigger in response_lower for trigger in escalation_triggers)

        return {
            **state,
            "should_escalate": should_escalate
        }

    async def process_query(
        self,
        query: str,
        creator_id: str,
        conversation_history: list = None
    ) -> dict:
        initial_state = AgentState(
            messages=conversation_history or [],
            context=[],
            query=query,
            creator_id=creator_id,
            response="",
            sources=[],
            should_escalate=False
        )

        final_state = await self.graph.ainvoke(initial_state)

        return {
            "response": final_state["response"],
            "sources": final_state["sources"],
            "should_escalate": final_state["should_escalate"],
            "context_used": len(final_state["context"])
        }
