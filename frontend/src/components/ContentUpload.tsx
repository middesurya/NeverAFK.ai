"use client";

import { useState } from "react";

interface ContentUploadProps {
  creatorId: string;
}

export default function ContentUpload({ creatorId }: ContentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [contentType, setContentType] = useState<string>("pdf");
  const [title, setTitle] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus("Please select a file");
      return;
    }

    setUploading(true);
    setUploadStatus("Uploading and processing...");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("creator_id", creatorId);
    formData.append("content_type", contentType);
    formData.append("title", title || file.name);

    try {
      const response = await fetch("http://localhost:8000/upload/content", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus(`Success! Processed ${data.chunks_created} content chunks.`);
        setFile(null);
        setTitle("");
      } else {
        setUploadStatus(`Error: ${data.detail || "Upload failed"}`);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus("Error: Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Upload Course Content</h2>
      <p className="text-gray-600 mb-6">
        Upload your course materials to train the AI assistant. Supported formats: PDF, video (MP4), text files.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Content Type
          </label>
          <select
            value={contentType}
            onChange={(e) => setContentType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="pdf">PDF Document</option>
            <option value="video">Video (will be transcribed)</option>
            <option value="text">Text File</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Title/Name
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Module 1: Introduction"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            File
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.txt,.mp4,.mov,.avi"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
        >
          {uploading ? "Processing..." : "Upload & Process"}
        </button>

        {uploadStatus && (
          <div
            className={`p-3 rounded-lg ${
              uploadStatus.startsWith("Success")
                ? "bg-green-50 text-green-800"
                : uploadStatus.startsWith("Error")
                ? "bg-red-50 text-red-800"
                : "bg-blue-50 text-blue-800"
            }`}
          >
            {uploadStatus}
          </div>
        )}
      </div>

      <div className="mt-6 pt-6 border-t">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Tips for best results:</h3>
        <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
          <li>Use clear, descriptive titles for each piece of content</li>
          <li>PDFs with good text formatting work best</li>
          <li>Video transcription may take several minutes</li>
          <li>Break large courses into smaller modules for better organization</li>
        </ul>
      </div>
    </div>
  );
}
