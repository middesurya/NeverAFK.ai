'use client';

import Link from 'next/link';

const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const ArrowLeftIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
  </svg>
);

export default function PricingPage() {
  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for trying out the platform",
      features: [
        "100 AI responses per month",
        "Basic support",
        "Single content upload",
        "Email notifications",
        "Community support",
      ],
      cta: "Start Free",
      highlighted: false,
      href: "/dashboard",
    },
    {
      name: "Starter",
      price: "$29",
      period: "per month",
      description: "For growing course creators",
      features: [
        "1,000 AI responses per month",
        "Unlimited content uploads",
        "Email support",
        "Custom widget styling",
        "Response analytics",
        "Priority processing",
      ],
      cta: "Start Trial",
      highlighted: true,
      href: "/dashboard",
    },
    {
      name: "Pro",
      price: "$49",
      period: "per month",
      description: "For established creators",
      features: [
        "Unlimited AI responses",
        "Unlimited content uploads",
        "Priority support",
        "Custom widget styling",
        "Advanced analytics",
        "API access",
        "White-label option",
        "Custom integrations",
      ],
      cta: "Start Trial",
      highlighted: false,
      href: "/dashboard",
    },
  ];

  const faqs = [
    {
      question: "How does the 14-day trial work?",
      answer: "Start with any paid plan and get full access for 14 days. No credit card required. Cancel anytime during the trial.",
    },
    {
      question: "What counts as an AI response?",
      answer: "Each time a student asks a question and receives an AI-generated answer, that counts as one response.",
    },
    {
      question: "Can I upgrade or downgrade anytime?",
      answer: "Yes! You can change your plan at any time. Changes take effect immediately, and we'll prorate any difference.",
    },
    {
      question: "What file formats do you support?",
      answer: "We support PDF, TXT, DOCX, MP4, MOV, and AVI files. Video files are automatically transcribed.",
    },
  ];

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] relative overflow-hidden">
      {/* Background Effects */}
      <div className="orb-violet -top-[300px] left-[20%] opacity-20" />
      <div className="orb-cyan top-[400px] -right-[200px] opacity-15" />

      {/* Navigation */}
      <nav className="relative z-50 border-b border-[var(--color-border)]">
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

            <Link href="/" className="btn btn-ghost text-sm">
              <ArrowLeftIcon />
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10 py-16 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16 animate-fade-in-down">
          <div className="inline-flex items-center gap-2 badge mb-4">
            <span>Simple Pricing</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-[var(--color-text-primary)] mb-4">
            Choose your plan
          </h1>
          <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
            Start free and scale as you grow. All plans include a 14-day free trial.
            No credit card required.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto mb-20">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`card relative animate-fade-in-up ${
                plan.highlighted
                  ? "border-[var(--color-accent)] glow-strong scale-105 z-10"
                  : "border-[var(--color-border)]"
              }`}
              style={{ animationDelay: `${index * 100 + 100}ms` }}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="badge bg-gradient-to-r from-violet-500 to-cyan-500 text-white border-0 px-4">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-6 pt-4">
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
                  {plan.name}
                </h2>
                <div className="flex items-baseline justify-center gap-1 mb-2">
                  <span className="text-4xl font-bold text-[var(--color-text-primary)]">
                    {plan.price}
                  </span>
                  <span className="text-[var(--color-text-tertiary)]">
                    /{plan.period}
                  </span>
                </div>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {plan.description}
                </p>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                      plan.highlighted
                        ? "bg-[var(--color-accent)] text-white"
                        : "bg-[var(--color-accent-subtle)] text-[var(--color-accent-light)]"
                    }`}>
                      <CheckIcon />
                    </div>
                    <span className="text-sm text-[var(--color-text-secondary)]">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`btn w-full ${
                  plan.highlighted ? "btn-primary" : "btn-secondary"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)] text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="card">
                <h3 className="font-semibold text-[var(--color-text-primary)] mb-2">
                  {faq.question}
                </h3>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {faq.answer}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16">
          <p className="text-[var(--color-text-secondary)] mb-4">
            Have questions? Need a custom plan?
          </p>
          <Link href="/demo" className="btn btn-ghost">
            Contact Sales
          </Link>
        </div>
      </main>
    </div>
  );
}
