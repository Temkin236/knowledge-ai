import React, { useRef, useState } from "react";
import { UploadCloud, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "../ui/Button";
import { cn } from "../../lib/utils";

interface DocumentDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
}

export const DocumentDropzone: React.FC<DocumentDropzoneProps> = ({
  onUpload,
  isUploading = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = [".pdf", ".docx", ".txt", ".md"];
  const maxSizeBytes = 20 * 1024 * 1024; // 20 MB

  const validateAndUpload = async (file: File) => {
    setError(null);
    setSuccess(null);

    const ext = `.${file.name.split(".").pop()?.toLowerCase()}`;
    if (!allowedExtensions.includes(ext)) {
      setError(`Unsupported file type (${ext}). Allowed: PDF, DOCX, TXT, MD.`);
      return;
    }

    if (file.size > maxSizeBytes) {
      setError(`File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds 20MB limit.`);
      return;
    }

    try {
      await onUpload(file);
      setSuccess(`Uploaded ${file.name}! Indexing in progress...`);
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.message || "Upload failed.");
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-dashed transition-all cursor-pointer text-center",
          isDragOver
            ? "border-emerald-500 bg-emerald-500/5 scale-[0.99]"
            : "border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/80 hover:border-zinc-700"
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              validateAndUpload(e.target.files[0]);
            }
          }}
        />

        <div className="w-12 h-12 rounded-xl bg-zinc-800/80 flex items-center justify-center text-emerald-400 mb-3 border border-zinc-700/60 shadow-inner">
          <UploadCloud className="w-6 h-6" />
        </div>

        <p className="text-sm font-semibold text-zinc-100 mb-1">
          Click to upload or drag & drop documents
        </p>
        <p className="text-xs text-zinc-400 mb-4 max-w-sm">
          Supports PDF, DOCX, TXT, and Markdown files up to 20MB each.
        </p>

        <Button
          type="button"
          size="sm"
          variant="secondary"
          isLoading={isUploading}
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
        >
          Select Document
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 text-xs text-red-400 bg-red-950/30 border border-red-900/50 rounded-xl">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 p-3 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-900/50 rounded-xl">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{success}</span>
        </div>
      )}
    </div>
  );
};
