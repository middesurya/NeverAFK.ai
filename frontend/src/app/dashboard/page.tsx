"use client";

import { useState, useEffect } from "react";
import EmbedWidgetGenerator from "@/components/EmbedWidget";

interface Conversation {
  id: string;
  student_message: string;
  ai_response: string;
  sources: string[];
  should_escalate: boolean;
  reviewed: boolean;
  created_at: string;
}

export default function DashboardPage() {
  const creatorId = "demo-creator-id";
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<"overview" | "conversations" | "embed">("overview");

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await fetch(`http://localhost:8000/conversations/${creatorId}`);
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Creator Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage your AI support assistant</p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              <button
                onClick={() => setSelectedTab("overview")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === "overview"
                    ? "border-indigo-500 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setSelectedTab("conversations")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === "conversations"
                    ? "border-indigo-500 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Conversations
              </button>
              <button
                onClick={() => setSelectedTab("embed")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === "embed"
                    ? "border-indigo-500 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Embed Widget
              </button>
            </nav>
          </div>
        </div>

        {selectedTab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Conversations</h3>
              <p className="text-4xl font-bold text-indigo-600">{conversations.length}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Needs Review</h3>
              <p className="text-4xl font-bold text-orange-600">
                {conversations.filter(c => c.should_escalate && !c.reviewed).length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Credits Remaining</h3>
              <p className="text-4xl font-bold text-green-600">100</p>
            </div>
          </div>
        )}

        {selectedTab === "conversations" && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4">Recent Conversations</h2>
              {loading ? (
                <p className="text-gray-500">Loading conversations...</p>
              ) : conversations.length === 0 ? (
                <p className="text-gray-500">No conversations yet</p>
              ) : (
                <div className="space-y-4">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`border rounded-lg p-4 ${
                        conv.should_escalate ? "border-orange-300 bg-orange-50" : "border-gray-200"
                      }`}
                    >
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-500">Student Question</span>
                          {conv.should_escalate && (
                            <span className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
                              Needs Review
                            </span>
                          )}
                        </div>
                        <p className="text-gray-900">{conv.student_message}</p>
                      </div>

                      <div className="mb-3">
                        <span className="text-sm font-medium text-gray-500 block mb-2">AI Response</span>
                        <p className="text-gray-700">{conv.ai_response}</p>
                      </div>

                      {conv.sources && conv.sources.length > 0 && (
                        <div>
                          <span className="text-xs text-gray-500 block mb-1">Sources:</span>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {conv.sources.map((source, idx) => (
                              <li key={idx}>{source}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === "embed" && (
          <EmbedWidgetGenerator creatorId={creatorId} />
        )}
      </div>
    </main>
  );
}
