"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

interface ChatInterfaceProps {
  creatorId: string;
}

// Icons
const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const SparklesIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const BotIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

export default function ChatInterface({ creatorId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          creator_id: creatorId,
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        sources: data.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I encountered an error connecting to the server. Please make sure the backend is running and try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestedQuestions = [
    "What topics does this course cover?",
    "How do I get started?",
    "What are the prerequisites?",
  ];

  return (
    <div className="flex flex-col h-[650px] w-full max-w-2xl rounded-2xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-bg-secondary)] shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-[var(--color-border)] bg-gradient-to-r from-[var(--color-bg-tertiary)] to-[var(--color-bg-secondary)]">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center text-white animate-pulse-glow">
          <BotIcon />
        </div>
        <div>
          <h2 className="font-semibold text-[var(--color-text-primary)]">AI Support Assistant</h2>
          <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-tertiary)]">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>Online &middot; Typically responds instantly</span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 flex items-center justify-center mb-4">
              <SparklesIcon />
            </div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
              How can I help you today?
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6 max-w-sm">
              Ask me anything about the course content, assignments, or policies. I&apos;m here to help 24/7.
            </p>

            {/* Suggested Questions */}
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => setInput(question)}
                  className="px-3 py-1.5 text-xs rounded-full border border-[var(--color-border-accent)] text-[var(--color-accent-light)] hover:bg-[var(--color-accent-subtle)] transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 animate-fade-in-up ${
                  message.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    message.role === "user"
                      ? "bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]"
                      : "bg-gradient-to-br from-violet-500 to-cyan-500 text-white"
                  }`}
                >
                  {message.role === "user" ? <UserIcon /> : <BotIcon />}
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-violet-600 to-violet-500 text-white rounded-tr-sm"
                      : "bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] rounded-tl-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
                      <div className="flex items-center gap-1.5 text-xs text-[var(--color-accent-light)]">
                        <SparklesIcon />
                        <span className="font-medium">Sources:</span>
                      </div>
                      <ul className="mt-1.5 space-y-1">
                        {message.sources.map((source, idx) => (
                          <li key={idx} className="text-xs text-[var(--color-text-tertiary)]">
                            {source}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex items-start gap-3 animate-fade-in">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center text-white">
                  <BotIcon />
                </div>
                <div className="bg-[var(--color-bg-tertiary)] rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] typing-dot" />
                    <span className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] typing-dot" />
                    <span className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] typing-dot" />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-primary)]">
        <div className="flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question..."
            className="input flex-1 bg-[var(--color-bg-secondary)] py-3"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="btn btn-primary p-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            <SendIcon />
          </button>
        </div>
        <p className="text-xs text-[var(--color-text-muted)] text-center mt-3">
          Powered by AI &middot; Responses are based on course content
        </p>
      </div>
    </div>
  );
}
