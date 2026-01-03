from typing import List, Dict, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
import os


class VectorStoreService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=1024,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = "strongmvp"
        self.pc = Pinecone(api_key=self.pinecone_api_key)

    def initialize_pinecone(self):
        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        return self.pc.Index(self.index_name)

    async def add_documents(
        self,
        documents: List[Document],
        creator_id: str,
        namespace: Optional[str] = None
    ) -> Dict:
        namespace = namespace or creator_id

        vectorstore = PineconeVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
            index_name=self.index_name,
            namespace=namespace
        )

        return {
            "status": "success",
            "document_count": len(documents),
            "namespace": namespace
        }

    async def similarity_search(
        self,
        query: str,
        creator_id: str,
        k: int = 4,
        namespace: Optional[str] = None
    ) -> List[Document]:
        namespace = namespace or creator_id

        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=namespace
        )

        results = vectorstore.similarity_search_with_score(query, k=k)
        return results
