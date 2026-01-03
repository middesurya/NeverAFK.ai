'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Creator Support AI
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            AI customer support that actually understands your course content.
            Answer student questions 24/7 with RAG-powered intelligence.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-3xl mb-4">📚</div>
            <h3 className="text-xl font-semibold mb-2">Content Aware</h3>
            <p className="text-gray-600">
              Indexes your course videos, PDFs, and materials to answer specific
              content questions
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-3xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold mb-2">Instant Responses</h3>
            <p className="text-gray-600">
              Students get accurate answers at 3am without waiting for you
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-3xl mb-4">✅</div>
            <h3 className="text-xl font-semibold mb-2">Creator Control</h3>
            <p className="text-gray-600">
              Review all AI responses and improve accuracy over time
            </p>
          </div>
        </div>

        <div className="mt-16 text-center">
          <Link href="/demo">
            <button className="bg-indigo-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-700 transition">
              Get Early Access
            </button>
          </Link>
        </div>
      </div>
    </main>
  );
}
