'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ChatInterface from "@/components/ChatInterface";

const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const ArrowLeftIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
  </svg>
);

export default function DemoPage() {
  const { user } = useAuth();

  // Use logged-in user's ID if available, otherwise use demo-creator for public demo
  const creatorId = user?.id || "demo-creator";
  const isAuthenticated = !!user;

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] relative overflow-hidden">
      {/* Background Effects */}
      <div className="orb-violet top-[100px] -right-[200px] opacity-20" />
      <div className="orb-cyan -bottom-[100px] -left-[100px] opacity-15" />

      {/* Navigation */}
      <nav className="relative z-50 border-b border-[var(--color-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
                <SparklesIcon />
              </div>
              <span className="font-bold text-lg text-[var(--color-text-primary)]">
                Creator Support AI
              </span>
            </Link>

            <Link href="/" className="btn btn-ghost text-sm">
              <ArrowLeftIcon />
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-10 animate-fade-in-down">
            <div className="inline-flex items-center gap-2 badge mb-4">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span>{isAuthenticated ? 'Your Content' : 'Live Demo'}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[var(--color-text-primary)] mb-3">
              {isAuthenticated ? 'Chat Demo' : 'Try the AI Assistant'}
            </h1>
            <p className="text-[var(--color-text-secondary)] max-w-xl mx-auto">
              {isAuthenticated
                ? 'Test your AI assistant with the content you uploaded. Ask questions about your course materials.'
                : 'This demo is connected to sample course content. Ask questions about AI support, RAG systems, or anything covered in the training materials.'}
            </p>
          </div>

          {/* Chat Interface */}
          <div className="flex justify-center animate-fade-in-up" style={{ animationDelay: '200ms' }}>
            <ChatInterface creatorId={creatorId} />
          </div>

          {/* Tips Section */}
          <div className="mt-10 max-w-2xl mx-auto animate-fade-in-up" style={{ animationDelay: '400ms' }}>
            <div className="card bg-[var(--color-bg-secondary)]/50 border-[var(--color-border-accent)]">
              <h3 className="font-semibold text-[var(--color-text-primary)] mb-3 flex items-center gap-2">
                <SparklesIcon />
                Try asking:
              </h3>
              <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
                <li className="flex items-start gap-2">
                  <span className="text-[var(--color-accent-light)]">&bull;</span>
                  <span>&quot;What are the benefits of AI support?&quot;</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[var(--color-accent-light)]">&bull;</span>
                  <span>&quot;How does RAG work?&quot;</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[var(--color-accent-light)]">&bull;</span>
                  <span>&quot;What is AI-powered customer support?&quot;</span>
                </li>
              </ul>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-10 text-center animate-fade-in-up" style={{ animationDelay: '600ms' }}>
            <p className="text-[var(--color-text-tertiary)] text-sm mb-4">
              Ready to add AI support to your course?
            </p>
            <Link href="/dashboard" className="btn btn-primary">
              Get Started Free
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
