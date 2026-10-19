import React from "react";
import { X, FileText, Bookmark, Layers, Percent } from "lucide-react";
import { Citation } from "../../types";

interface SourceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citation: Citation | null;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({
  isOpen,
  onClose,
  citation,
}) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-zinc-900 border-l border-zinc-800 p-6 flex flex-col justify-between shadow-2xl">
          {/* Header */}
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold text-base text-zinc-100 truncate max-w-[280px]">
                  {citation.filename}
                </h3>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metadata Pills */}
            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
              {citation.page_number && (
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
                  <Bookmark className="w-4 h-4 text-zinc-400" />
                  <div>
                    <span className="text-zinc-500 block">Page</span>
                    <span className="font-semibold text-zinc-200">
                      Page {citation.page_number}
                    </span>
                  </div>
                </div>
              )}

              {citation.section_title && (
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
                  <Layers className="w-4 h-4 text-zinc-400" />
                  <div className="truncate">
                    <span className="text-zinc-500 block">Section</span>
                    <span className="font-semibold text-zinc-200 truncate block">
                      {citation.section_title}
                    </span>
                  </div>
                </div>
              )}

              {citation.similarity_score !== undefined && (
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
                  <Percent className="w-4 h-4 text-emerald-400" />
                  <div>
                    <span className="text-zinc-500 block">Retrieval Relevance</span>
                    <span className="font-semibold text-emerald-400 font-mono">
                      {Math.round(citation.similarity_score * 100)}% Match
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Verbatim Excerpt */}
            <div className="mt-6">
              <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                Grounding Evidence Excerpt
              </h4>
              <div className="relative p-4 rounded-xl bg-zinc-950 border border-zinc-800/90 text-sm leading-relaxed text-zinc-300 font-mono max-h-[380px] overflow-y-auto whitespace-pre-wrap select-text">
                "{citation.excerpt}"
              </div>
            </div>
          </div>

          {/* Footer identifier */}
          <div className="pt-4 border-t border-zinc-800 text-[11px] text-zinc-500 font-mono flex justify-between items-center">
            <span>Chunk ID: {citation.chunk_id.slice(0, 16)}...</span>
            <span className="text-emerald-500/80">Verified Grounding</span>
          </div>
        </div>
      </div>
    </div>
  );
};
