import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Creator Support AI - RAG-Powered Customer Support",
  description: "AI customer support that actually understands your content. Answer student questions 24/7 with intelligent, context-aware responses.",
  keywords: ["AI support", "customer support", "course creators", "RAG", "chatbot"],
  authors: [{ name: "Creator Support AI" }],
  openGraph: {
    title: "Creator Support AI",
    description: "AI customer support that actually understands your content",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body suppressHydrationWarning className="min-h-screen bg-[var(--color-bg-primary)] antialiased">
        {children}
      </body>
    </html>
  );
}
