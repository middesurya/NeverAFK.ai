"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import ContentUpload from "@/components/ContentUpload";
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

// Icons
const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const ChatIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const AlertIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);

const CreditIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const UploadIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const CodeIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>
);

const HomeIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

type Tab = "overview" | "conversations" | "upload" | "embed";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading, signOut, getAccessToken } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<Tab>("overview");

  // Use authenticated user's ID, fallback to demo-creator for unauthenticated demo
  const creatorId = user?.id || "demo-creator";

  // Redirect to login if not authenticated (after auth check completes)
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetchConversations();
    }
  }, [user]);

  const fetchConversations = async () => {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/conversations/${creatorId}`,
        { headers }
      );
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
  };

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[var(--color-bg-primary)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <SparklesIcon />
          </div>
          <p className="text-[var(--color-text-secondary)]">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render dashboard if not authenticated
  if (!user) {
    return null;
  }

  const tabs = [
    { id: "overview" as Tab, label: "Overview", icon: <HomeIcon /> },
    { id: "conversations" as Tab, label: "Conversations", icon: <ChatIcon /> },
    { id: "upload" as Tab, label: "Upload Content", icon: <UploadIcon /> },
    { id: "embed" as Tab, label: "Embed Widget", icon: <CodeIcon /> },
  ];

  const stats = [
    {
      label: "Total Conversations",
      value: conversations.length,
      icon: <ChatIcon />,
      color: "from-violet-500 to-violet-600",
    },
    {
      label: "Needs Review",
      value: conversations.filter((c) => c.should_escalate && !c.reviewed).length,
      icon: <AlertIcon />,
      color: "from-amber-500 to-orange-500",
    },
    {
      label: "Credits Remaining",
      value: 100,
      icon: <CreditIcon />,
      color: "from-emerald-500 to-green-500",
    },
  ];

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)]">
      {/* Navigation */}
      <nav className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
                <SparklesIcon />
              </div>
              <span className="font-bold text-lg text-[var(--color-text-primary)]">
                Creator Support AI
              </span>
            </Link>

            <div className="flex items-center gap-4">
              <span className="text-sm text-[var(--color-text-tertiary)] hidden sm:block">
                {user.email}
              </span>
              <Link href="/pricing" className="btn btn-secondary text-sm">
                Upgrade
              </Link>
              <button onClick={handleSignOut} className="btn btn-ghost text-sm">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 animate-fade-in-down">
          <h1 className="text-2xl sm:text-3xl font-bold text-[var(--color-text-primary)]">
            Dashboard
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Manage your AI support assistant and view analytics
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-8 overflow-x-auto">
          <div className="flex gap-1 p-1 bg-[var(--color-bg-secondary)] rounded-xl w-fit border border-[var(--color-border)]">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedTab === tab.id
                    ? "bg-gradient-to-r from-violet-500 to-violet-600 text-white shadow-lg"
                    : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]"
                }`}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="animate-fade-in-up">
          {selectedTab === "overview" && (
            <div className="space-y-8">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {stats.map((stat, index) => (
                  <div
                    key={index}
                    className="card card-hover"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm text-[var(--color-text-tertiary)] mb-1">
                          {stat.label}
                        </p>
                        <p className="text-3xl font-bold text-[var(--color-text-primary)]">
                          {stat.value}
                        </p>
                      </div>
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-white`}>
                        {stat.icon}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Quick Actions */}
              <div>
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                  Quick Actions
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <button
                    onClick={() => setSelectedTab("upload")}
                    className="card card-hover flex items-center gap-4 text-left"
                  >
                    <div className="w-12 h-12 rounded-xl bg-[var(--color-accent-subtle)] flex items-center justify-center text-[var(--color-accent-light)]">
                      <UploadIcon />
                    </div>
                    <div>
                      <h3 className="font-semibold text-[var(--color-text-primary)]">
                        Upload Content
                      </h3>
                      <p className="text-sm text-[var(--color-text-secondary)]">
                        Add course materials for AI training
                      </p>
                    </div>
                  </button>
                  <button
                    onClick={() => setSelectedTab("embed")}
                    className="card card-hover flex items-center gap-4 text-left"
                  >
                    <div className="w-12 h-12 rounded-xl bg-[var(--color-accent-subtle)] flex items-center justify-center text-[var(--color-accent-light)]">
                      <CodeIcon />
                    </div>
                    <div>
                      <h3 className="font-semibold text-[var(--color-text-primary)]">
                        Get Embed Code
                      </h3>
                      <p className="text-sm text-[var(--color-text-secondary)]">
                        Add the chat widget to your website
                      </p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Recent Activity */}
              {conversations.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      Recent Conversations
                    </h2>
                    <button
                      onClick={() => setSelectedTab("conversations")}
                      className="text-sm text-[var(--color-accent-light)] hover:underline"
                    >
                      View all
                    </button>
                  </div>
                  <div className="space-y-3">
                    {conversations.slice(0, 3).map((conv) => (
                      <div
                        key={conv.id}
                        className={`card ${conv.should_escalate ? "border-amber-500/30" : ""}`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-[var(--color-text-primary)] truncate">
                              {conv.student_message}
                            </p>
                            <p className="text-xs text-[var(--color-text-tertiary)] mt-1 line-clamp-2">
                              {conv.ai_response}
                            </p>
                          </div>
                          {conv.should_escalate && (
                            <span className="badge bg-amber-500/20 text-amber-400 border-amber-500/30">
                              Review
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {selectedTab === "conversations" && (
            <div>
              <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-6">
                All Conversations
              </h2>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="card animate-shimmer h-24" />
                  ))}
                </div>
              ) : conversations.length === 0 ? (
                <div className="card text-center py-12">
                  <div className="w-16 h-16 rounded-2xl bg-[var(--color-bg-tertiary)] flex items-center justify-center mx-auto mb-4">
                    <ChatIcon />
                  </div>
                  <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                    No conversations yet
                  </h3>
                  <p className="text-[var(--color-text-secondary)] mb-4">
                    Conversations will appear here once students start using your AI assistant.
                  </p>
                  <Link href="/demo" className="btn btn-primary">
                    Test the Demo
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`card ${conv.should_escalate ? "border-amber-500/30 bg-amber-500/5" : ""}`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <span className="text-xs font-medium text-[var(--color-text-tertiary)]">
                          Student Question
                        </span>
                        {conv.should_escalate && (
                          <span className="badge bg-amber-500/20 text-amber-400 border-amber-500/30">
                            <AlertIcon />
                            Needs Review
                          </span>
                        )}
                      </div>
                      <p className="text-[var(--color-text-primary)] mb-4">
                        {conv.student_message}
                      </p>

                      <div className="mb-3">
                        <span className="text-xs font-medium text-[var(--color-text-tertiary)]">
                          AI Response
                        </span>
                        <p className="text-[var(--color-text-secondary)] mt-1 text-sm">
                          {conv.ai_response}
                        </p>
                      </div>

                      {conv.sources && conv.sources.length > 0 && (
                        <div className="pt-3 border-t border-[var(--color-border)]">
                          <div className="flex items-center gap-1.5 text-xs text-[var(--color-accent-light)]">
                            <SparklesIcon />
                            <span>Sources: {conv.sources.join(", ")}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {selectedTab === "upload" && (
            <ContentUpload creatorId={creatorId} authToken={getAccessToken()} />
          )}

          {selectedTab === "embed" && (
            <EmbedWidgetGenerator creatorId={creatorId} />
          )}
        </div>
      </div>
    </div>
  );
}
