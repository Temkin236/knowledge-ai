import React from "react";
import { BookOpen } from "lucide-react";
import { Citation } from "../../types";

interface CitationBadgeProps {
  citation: Citation;
  index?: number;
  onClick: (citation: Citation) => void;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({
  citation,
  index,
  onClick,
}) => {
  const label = citation.filename.length > 20
    ? `${citation.filename.slice(0, 18)}...`
    : citation.filename;

  const pageStr = citation.page_number ? `, p. ${citation.page_number}` : "";

  return (
    <button
      type="button"
      onClick={() => onClick(citation)}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-zinc-800/90 text-emerald-400 border border-zinc-700/80 hover:bg-zinc-800 hover:border-emerald-500/50 hover:text-emerald-300 transition-all cursor-pointer shadow-sm shadow-black/20"
      title={`Click to inspect source: ${citation.filename}`}
    >
      <BookOpen className="w-3.5 h-3.5 text-emerald-500" />
      <span>
        {index !== undefined && <span className="text-zinc-500 font-mono mr-1">[{index + 1}]</span>}
        {label}
        {pageStr}
      </span>
      {citation.similarity_score !== undefined && (
        <span className="text-[10px] text-zinc-400 font-mono bg-zinc-900 px-1 py-0.5 rounded">
          {Math.round(citation.similarity_score * 100)}%
        </span>
      )}
    </button>
  );
};
