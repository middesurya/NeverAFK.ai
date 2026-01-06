'use client';

import Link from 'next/link';
import { useState } from 'react';

// Icons
const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const BrainIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ShieldIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const ChartIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const CodeIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
  </svg>
);

const MenuIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const XIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const features = [
    {
      icon: <BrainIcon />,
      title: "Content-Aware AI",
      description: "Our RAG system actually reads and understands your course materials, PDFs, and videos to provide accurate, contextual answers.",
    },
    {
      icon: <ClockIcon />,
      title: "24/7 Instant Support",
      description: "Students get answers at 3am without waiting for you. Reduce response time from hours to seconds.",
    },
    {
      icon: <ShieldIcon />,
      title: "Creator Control",
      description: "Review all AI responses, flag uncertain answers for human review, and improve accuracy over time.",
    },
    {
      icon: <ChartIcon />,
      title: "Analytics & Insights",
      description: "Understand what students are asking, identify knowledge gaps, and improve your content.",
    },
    {
      icon: <CodeIcon />,
      title: "Easy Integration",
      description: "Add our widget to any platform with a single line of code. Works with Teachable, Kajabi, Thinkific, and more.",
    },
    {
      icon: <SparklesIcon />,
      title: "Source Citations",
      description: "Every answer includes references to specific modules and timestamps, building student trust.",
    },
  ];

  const stats = [
    { value: "95%", label: "Questions answered" },
    { value: "<3s", label: "Average response time" },
    { value: "24/7", label: "Always available" },
    { value: "10x", label: "Support cost reduction" },
  ];

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] relative overflow-hidden">
      {/* Background Effects */}
      <div className="orb-violet -top-[200px] -left-[200px] opacity-30" />
      <div className="orb-cyan top-[400px] -right-[100px] opacity-20" />
      <div className="orb-violet bottom-[200px] left-[30%] opacity-20" />

      {/* Navigation */}
      <nav className="relative z-50 border-b border-[var(--color-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
                <SparklesIcon />
              </div>
              <span className="font-bold text-lg text-[var(--color-text-primary)]">
                Creator Support AI
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              <Link href="/demo" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                Demo
              </Link>
              <Link href="/pricing" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                Pricing
              </Link>
              <Link href="/dashboard" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                Dashboard
              </Link>
            </div>

            {/* CTA Buttons */}
            <div className="hidden md:flex items-center gap-4">
              <Link href="/demo" className="btn btn-ghost text-sm">
                Try Demo
              </Link>
              <Link href="/dashboard" className="btn btn-primary text-sm">
                Get Started
                <ArrowRightIcon />
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-[var(--color-text-secondary)]"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <XIcon /> : <MenuIcon />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden absolute top-16 inset-x-0 bg-[var(--color-bg-secondary)] border-b border-[var(--color-border)] p-4 animate-fade-in-down">
            <div className="flex flex-col gap-4">
              <Link href="/demo" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors py-2">
                Demo
              </Link>
              <Link href="/pricing" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors py-2">
                Pricing
              </Link>
              <Link href="/dashboard" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors py-2">
                Dashboard
              </Link>
              <Link href="/dashboard" className="btn btn-primary w-full mt-2">
                Get Started
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 badge mb-8 animate-fade-in-down opacity-0" style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}>
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>Now with GPT-4 Turbo</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6 animate-fade-in-up opacity-0" style={{ animationDelay: '200ms', animationFillMode: 'forwards' }}>
            <span className="text-[var(--color-text-primary)]">AI Support That</span>
            <br />
            <span className="gradient-text">Actually Understands</span>
            <br />
            <span className="text-[var(--color-text-primary)]">Your Content</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg sm:text-xl text-[var(--color-text-secondary)] max-w-2xl mx-auto mb-10 animate-fade-in-up opacity-0" style={{ animationDelay: '300ms', animationFillMode: 'forwards' }}>
            Stop answering the same questions over and over. Let AI handle student support 24/7 with accurate,
            context-aware responses based on your actual course content.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fade-in-up opacity-0" style={{ animationDelay: '400ms', animationFillMode: 'forwards' }}>
            <Link href="/demo" className="btn btn-primary px-8 py-4 text-base">
              Try Live Demo
              <ArrowRightIcon />
            </Link>
            <Link href="/pricing" className="btn btn-secondary px-8 py-4 text-base">
              View Pricing
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto animate-fade-in-up opacity-0" style={{ animationDelay: '500ms', animationFillMode: 'forwards' }}>
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold gradient-text mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-[var(--color-text-tertiary)]">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Preview */}
      <section className="relative z-10 pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="card border-glow glow p-1 rounded-2xl animate-fade-in-up opacity-0" style={{ animationDelay: '600ms', animationFillMode: 'forwards' }}>
            <div className="bg-[var(--color-bg-secondary)] rounded-xl overflow-hidden">
              {/* Browser Chrome */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--color-border)]">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <div className="w-3 h-3 rounded-full bg-green-500/80" />
                </div>
                <div className="flex-1 ml-4">
                  <div className="bg-[var(--color-bg-tertiary)] rounded-md px-3 py-1 text-xs text-[var(--color-text-tertiary)] text-center max-w-xs mx-auto">
                    your-course-site.com
                  </div>
                </div>
              </div>

              {/* Chat Preview */}
              <div className="p-6 space-y-4">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-gradient-to-r from-violet-600 to-violet-500 text-white px-4 py-2 rounded-2xl rounded-br-sm max-w-xs">
                    How do I export my project to PDF?
                  </div>
                </div>

                {/* AI Response */}
                <div className="flex justify-start">
                  <div className="bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] px-4 py-3 rounded-2xl rounded-bl-sm max-w-md">
                    <p className="mb-2">To export your project to PDF, follow these steps:</p>
                    <ol className="list-decimal list-inside text-sm text-[var(--color-text-secondary)] space-y-1 mb-3">
                      <li>Go to File &rarr; Export</li>
                      <li>Select &quot;PDF&quot; from the format dropdown</li>
                      <li>Choose your quality settings</li>
                      <li>Click &quot;Export&quot;</li>
                    </ol>
                    <div className="flex items-center gap-2 text-xs text-[var(--color-accent-light)] mt-2 pt-2 border-t border-[var(--color-border)]">
                      <SparklesIcon />
                      <span>Source: Module 3 - Exporting (2:34)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 py-24 px-4 sm:px-6 lg:px-8 border-t border-[var(--color-border)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[var(--color-text-primary)] mb-4">
              Everything you need for intelligent support
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Built specifically for course creators who want to scale their support without sacrificing quality.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="card card-hover group animate-fade-in-up opacity-0"
                style={{ animationDelay: `${index * 100 + 100}ms`, animationFillMode: 'forwards' }}
              >
                <div className="w-12 h-12 rounded-xl bg-[var(--color-accent-subtle)] flex items-center justify-center text-[var(--color-accent-light)] mb-4 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                  {feature.title}
                </h3>
                <p className="text-[var(--color-text-secondary)] text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="relative z-10 py-24 px-4 sm:px-6 lg:px-8 bg-[var(--color-bg-secondary)]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[var(--color-text-primary)] mb-4">
              Get started in minutes
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)]">
              Three simple steps to transform your support
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Upload Content",
                description: "Upload your course videos, PDFs, and documents. Our AI processes and indexes everything.",
              },
              {
                step: "02",
                title: "Embed Widget",
                description: "Copy one line of code to add the chat widget to your course platform or website.",
              },
              {
                step: "03",
                title: "Relax",
                description: "Students get instant, accurate answers 24/7. You review and improve as needed.",
              },
            ].map((item, index) => (
              <div key={index} className="relative">
                <div className="text-6xl font-bold gradient-text opacity-20 absolute -top-4 -left-2">
                  {item.step}
                </div>
                <div className="relative pt-8">
                  <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
                    {item.title}
                  </h3>
                  <p className="text-[var(--color-text-secondary)]">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-[var(--color-text-primary)] mb-4">
            Ready to transform your support?
          </h2>
          <p className="text-lg text-[var(--color-text-secondary)] mb-8">
            Join course creators who are saving hours every week with AI-powered support.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/demo" className="btn btn-primary px-8 py-4 text-base">
              Try Live Demo
              <ArrowRightIcon />
            </Link>
            <Link href="/pricing" className="btn btn-secondary px-8 py-4 text-base">
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-[var(--color-border)] py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
                <SparklesIcon />
              </div>
              <span className="font-semibold text-[var(--color-text-primary)]">
                Creator Support AI
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm text-[var(--color-text-tertiary)]">
              <Link href="/demo" className="hover:text-[var(--color-text-primary)] transition-colors">
                Demo
              </Link>
              <Link href="/pricing" className="hover:text-[var(--color-text-primary)] transition-colors">
                Pricing
              </Link>
              <Link href="/dashboard" className="hover:text-[var(--color-text-primary)] transition-colors">
                Dashboard
              </Link>
            </div>
            <p className="text-sm text-[var(--color-text-muted)]">
              &copy; 2024 Creator Support AI
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
