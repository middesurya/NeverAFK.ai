"use client";

import { useState } from "react";

interface EmbedWidgetGeneratorProps {
  creatorId: string;
}

// Icons
const CopyIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const CodeIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>
);

export default function EmbedWidgetGenerator({ creatorId }: EmbedWidgetGeneratorProps) {
  const [copied, setCopied] = useState(false);
  const [position, setPosition] = useState("bottom-right");
  const [primaryColor, setPrimaryColor] = useState("#8b5cf6");
  const [welcomeMessage, setWelcomeMessage] = useState("Hi! How can I help you today?");

  const embedCode = `<!-- Creator Support AI Widget -->
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'https://your-domain.com/embed.js';
    script.setAttribute('data-creator-id', '${creatorId}');
    script.setAttribute('data-position', '${position}');
    script.setAttribute('data-color', '${primaryColor}');
    script.setAttribute('data-welcome', '${welcomeMessage}');
    script.async = true;
    document.head.appendChild(script);
  })();
</script>`;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const positions = [
    { value: "bottom-right", label: "Bottom Right" },
    { value: "bottom-left", label: "Bottom Left" },
    { value: "top-right", label: "Top Right" },
    { value: "top-left", label: "Top Left" },
  ];

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          Embed Widget Code
        </h2>
        <p className="text-[var(--color-text-secondary)] text-sm">
          Copy and paste this code snippet into your website to add the AI support chat.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Code Preview */}
        <div className="lg:col-span-2">
          <div className="card bg-[#0d1117] border-[var(--color-border)] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--color-border)] bg-[var(--color-bg-tertiary)]">
              <div className="flex items-center gap-2 text-[var(--color-text-tertiary)]">
                <CodeIcon />
                <span className="text-sm font-medium">HTML</span>
              </div>
              <button
                onClick={copyToClipboard}
                className={`btn text-sm py-1.5 ${
                  copied
                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                    : "btn-secondary"
                }`}
              >
                {copied ? (
                  <>
                    <CheckIcon />
                    Copied!
                  </>
                ) : (
                  <>
                    <CopyIcon />
                    Copy Code
                  </>
                )}
              </button>
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="text-sm text-[#c9d1d9] font-mono leading-relaxed">
                <code>{embedCode}</code>
              </pre>
            </div>
          </div>
        </div>

        {/* Customization Options */}
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-3">
              Widget Position
            </label>
            <div className="grid grid-cols-2 gap-2">
              {positions.map((pos) => (
                <button
                  key={pos.value}
                  onClick={() => setPosition(pos.value)}
                  className={`card py-3 text-sm text-center transition-all ${
                    position === pos.value
                      ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)] text-[var(--color-text-primary)]"
                      : "text-[var(--color-text-secondary)] hover:border-[var(--color-border-accent)]"
                  }`}
                >
                  {pos.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
              Primary Color
            </label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="w-12 h-12 rounded-lg border border-[var(--color-border)] cursor-pointer bg-transparent"
              />
              <input
                type="text"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="input flex-1 font-mono text-sm"
              />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
              Welcome Message
            </label>
            <textarea
              value={welcomeMessage}
              onChange={(e) => setWelcomeMessage(e.target.value)}
              className="input min-h-[100px] resize-none"
              rows={3}
            />
          </div>

          {/* Preview */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
              Preview
            </label>
            <div className="card bg-[var(--color-bg-tertiary)] h-32 relative overflow-hidden">
              <div
                className={`absolute ${
                  position.includes("bottom") ? "bottom-3" : "top-3"
                } ${position.includes("right") ? "right-3" : "left-3"}`}
              >
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center text-white shadow-lg cursor-pointer hover:scale-110 transition-transform"
                  style={{ backgroundColor: primaryColor }}
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Installation Instructions */}
      <div className="mt-8 card bg-[var(--color-bg-tertiary)]/50">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">
          Installation Instructions
        </h3>
        <ol className="space-y-3 text-sm text-[var(--color-text-secondary)]">
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent-light)] flex items-center justify-center flex-shrink-0 text-xs font-bold">
              1
            </span>
            <span>Copy the code snippet above</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent-light)] flex items-center justify-center flex-shrink-0 text-xs font-bold">
              2
            </span>
            <span>Paste it into your website&apos;s HTML, just before the closing <code className="bg-[var(--color-bg-tertiary)] px-1.5 py-0.5 rounded text-[var(--color-accent-light)]">&lt;/body&gt;</code> tag</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent-light)] flex items-center justify-center flex-shrink-0 text-xs font-bold">
              3
            </span>
            <span>The chat widget will appear automatically on your site</span>
          </li>
        </ol>
        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
          <p className="text-sm text-amber-400">
            <strong>Note:</strong> Replace <code className="bg-[var(--color-bg-tertiary)] px-1 py-0.5 rounded">your-domain.com</code> with your actual deployment URL after deploying.
          </p>
        </div>
      </div>
    </div>
  );
}
