"use client";

import { useState } from "react";

interface ContentUploadProps {
  creatorId: string;
}

// Icons
const UploadIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const FileIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const CheckCircleIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XCircleIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const SpinnerIcon = () => (
  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
  </svg>
);

export default function ContentUpload({ creatorId }: ContentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [contentType, setContentType] = useState<string>("pdf");
  const [title, setTitle] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ""));
      }
      setUploadStatus(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      if (!title) {
        setTitle(droppedFile.name.replace(/\.[^/.]+$/, ""));
      }
      setUploadStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus({ type: "error", message: "Please select a file" });
      return;
    }

    setUploading(true);
    setUploadStatus({ type: "info", message: "Uploading and processing..." });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("creator_id", creatorId);
    formData.append("content_type", contentType);
    formData.append("title", title || file.name);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/upload/content`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus({ type: "success", message: `Success! Processed ${data.chunks_created} content chunks.` });
        setFile(null);
        setTitle("");
      } else {
        setUploadStatus({ type: "error", message: data.detail || "Upload failed" });
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus({ type: "error", message: "Failed to upload file. Please check if the backend is running." });
    } finally {
      setUploading(false);
    }
  };

  const contentTypes = [
    { value: "pdf", label: "PDF Document", icon: "📄" },
    { value: "video", label: "Video (will be transcribed)", icon: "🎬" },
    { value: "text", label: "Text File", icon: "📝" },
  ];

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          Upload Course Content
        </h2>
        <p className="text-[var(--color-text-secondary)] text-sm">
          Upload your course materials to train the AI assistant. Supported formats: PDF, video (MP4), text files.
        </p>
      </div>

      <div className="space-y-6">
        {/* Content Type Selection */}
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-3">
            Content Type
          </label>
          <div className="grid grid-cols-3 gap-3">
            {contentTypes.map((type) => (
              <button
                key={type.value}
                onClick={() => setContentType(type.value)}
                className={`card text-center py-4 transition-all ${
                  contentType === type.value
                    ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                    : "hover:border-[var(--color-border-accent)]"
                }`}
              >
                <span className="text-2xl mb-2 block">{type.icon}</span>
                <span className="text-xs text-[var(--color-text-secondary)]">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Title Input */}
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
            Title / Name
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Module 1: Introduction"
            className="input"
          />
        </div>

        {/* File Upload Area */}
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
            File
          </label>
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`card border-2 border-dashed text-center py-10 transition-all cursor-pointer ${
              dragActive
                ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)]"
                : "hover:border-[var(--color-border-accent)]"
            }`}
          >
            <input
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.txt,.mp4,.mov,.avi"
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-2xl bg-[var(--color-accent-subtle)] flex items-center justify-center text-[var(--color-accent-light)] mb-4">
                  <UploadIcon />
                </div>
                <p className="text-[var(--color-text-primary)] font-medium mb-1">
                  {file ? file.name : "Drop your file here or click to browse"}
                </p>
                <p className="text-sm text-[var(--color-text-tertiary)]">
                  {file
                    ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                    : "PDF, TXT, MP4, MOV, AVI up to 100MB"}
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Selected File Info */}
        {file && (
          <div className="card bg-[var(--color-bg-tertiary)] flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-accent-subtle)] flex items-center justify-center text-[var(--color-accent-light)]">
              <FileIcon />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                {file.name}
              </p>
              <p className="text-xs text-[var(--color-text-tertiary)]">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={() => setFile(null)}
              className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)]"
            >
              <XCircleIcon />
            </button>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="btn btn-primary w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? (
            <>
              <SpinnerIcon />
              Processing...
            </>
          ) : (
            <>
              <UploadIcon />
              Upload & Process
            </>
          )}
        </button>

        {/* Status Message */}
        {uploadStatus && (
          <div
            className={`card flex items-center gap-3 ${
              uploadStatus.type === "success"
                ? "bg-green-500/10 border-green-500/30"
                : uploadStatus.type === "error"
                ? "bg-red-500/10 border-red-500/30"
                : "bg-blue-500/10 border-blue-500/30"
            }`}
          >
            {uploadStatus.type === "success" ? (
              <CheckCircleIcon />
            ) : uploadStatus.type === "error" ? (
              <XCircleIcon />
            ) : (
              <SpinnerIcon />
            )}
            <span
              className={`text-sm ${
                uploadStatus.type === "success"
                  ? "text-green-400"
                  : uploadStatus.type === "error"
                  ? "text-red-400"
                  : "text-blue-400"
              }`}
            >
              {uploadStatus.message}
            </span>
          </div>
        )}

        {/* Tips */}
        <div className="card bg-[var(--color-bg-tertiary)]/50">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">
            Tips for best results
          </h3>
          <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-accent-light)]">&bull;</span>
              Use clear, descriptive titles for each piece of content
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-accent-light)]">&bull;</span>
              PDFs with good text formatting work best
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-accent-light)]">&bull;</span>
              Video transcription may take several minutes
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-accent-light)]">&bull;</span>
              Break large courses into smaller modules for better organization
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
