import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Creator Support AI - RAG-Powered Customer Support",
  description: "AI customer support that actually understands your content",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
