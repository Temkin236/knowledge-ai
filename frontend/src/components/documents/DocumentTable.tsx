import React from "react";
import { FileText, Trash2, RotateCw, AlertTriangle, Layers } from "lucide-react";
import { Document } from "../../types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { formatBytes, formatDate } from "../../lib/utils";

interface DocumentTableProps {
  documents: Document[];
  onDelete: (id: string) => void;
  onRetry: (id: string) => void;
  isLoading?: boolean;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  onDelete,
  onRetry,
  isLoading = false,
}) => {
  if (documents.length === 0 && !isLoading) {
    return (
      <div className="text-center py-12 border border-zinc-800/80 rounded-2xl bg-zinc-900/30">
        <FileText className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-zinc-300">No documents indexed yet</h4>
        <p className="text-xs text-zinc-500 mt-1">
          Upload PDF, DOCX, TXT, or Markdown documents to begin chatting with them.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
      <table className="w-full text-left text-xs text-zinc-300">
        <thead className="bg-zinc-900 border-b border-zinc-800 text-zinc-400 font-medium">
          <tr>
            <th className="py-3 px-4">Document</th>
            <th className="py-3 px-4">Format / Size</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4">Chunks</th>
            <th className="py-3 px-4">Uploaded</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/60">
          {documents.map((doc) => {
            const ext = doc.filename.split(".").pop()?.toUpperCase() || "DOC";
            const isFailed = doc.status === "FAILED";

            return (
              <tr key={doc.id} className="hover:bg-zinc-800/30 transition-colors">
                <td className="py-3 px-4 font-medium text-zinc-100 flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                  <div className="truncate max-w-[220px]">
                    <span className="block truncate">{doc.filename}</span>
                    {isFailed && doc.error_message && (
                      <span className="text-[11px] text-red-400 flex items-center gap-1 mt-0.5 truncate">
                        <AlertTriangle className="w-3 h-3 shrink-0" />
                        {doc.error_message}
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-zinc-800 text-zinc-300 mr-2">
                    {ext}
                  </span>
                  <span>{formatBytes(doc.file_size)}</span>
                </td>
                <td className="py-3 px-4">
                  <Badge status={doc.status} />
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center gap-1 font-mono text-zinc-300">
                    <Layers className="w-3.5 h-3.5 text-zinc-500" />
                    {doc.chunk_count}
                  </span>
                </td>
                <td className="py-3 px-4 text-zinc-400">{formatDate(doc.created_at)}</td>
                <td className="py-3 px-4 text-right space-x-2">
                  {isFailed && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onRetry(doc.id)}
                      className="h-7 px-2 text-xs text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
                      title="Retry processing"
                    >
                      <RotateCw className="w-3 h-3 mr-1" />
                      Retry
                    </Button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete ${doc.filename}?`)) {
                        onDelete(doc.id);
                      }
                    }}
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-950/20 transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
