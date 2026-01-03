"use client";

import { useState } from "react";

interface EmbedWidgetGeneratorProps {
  creatorId: string;
}

export default function EmbedWidgetGenerator({ creatorId }: EmbedWidgetGeneratorProps) {
  const [copied, setCopied] = useState(false);

  const embedCode = `<!-- Creator Support AI Widget -->
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'http://localhost:3000/embed.js';
    script.setAttribute('data-creator-id', '${creatorId}');
    script.async = true;
    document.head.appendChild(script);
  })();
</script>`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Embed Widget Code</h2>
      <p className="text-gray-600 mb-4">
        Copy and paste this code snippet into your website to add the AI support chat.
      </p>

      <div className="bg-gray-900 text-green-400 p-4 rounded-lg mb-4 overflow-x-auto">
        <pre className="text-sm">
          <code>{embedCode}</code>
        </pre>
      </div>

      <button
        onClick={copyToClipboard}
        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
      >
        {copied ? "Copied!" : "Copy to Clipboard"}
      </button>

      <div className="mt-6 pt-6 border-t">
        <h3 className="text-lg font-semibold mb-3">Customization Options</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Widget Position
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option>Bottom Right</option>
              <option>Bottom Left</option>
              <option>Top Right</option>
              <option>Top Left</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Primary Color
            </label>
            <input
              type="color"
              defaultValue="#4F46E5"
              className="w-full h-10 rounded-lg border border-gray-300"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Welcome Message
            </label>
            <textarea
              defaultValue="Hi! How can I help you today?"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
