import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Bot, User, Copy, Check, Sparkles } from "lucide-react";
import { Citation, Message } from "../../types";
import { CitationBadge } from "../citations/CitationBadge";
import { cn } from "../../lib/utils";

interface ChatMessageProps {
  message: Message;
  onSelectCitation: (citation: Citation) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onSelectCitation,
}) => {
  const isAssistant = message.role === "assistant";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "group flex gap-4 px-4 py-5 rounded-2xl transition-colors",
        isAssistant
          ? "bg-zinc-900/40 border border-zinc-800/60"
          : "bg-transparent"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm",
          isAssistant
            ? "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30"
            : "bg-zinc-800 text-zinc-300 border border-zinc-700/60"
        )}
      >
        {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div className="flex-1 space-y-3 overflow-hidden">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
            {isAssistant ? (
              <>
                <span>Knowledge AI</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Grounded
                </span>
              </>
            ) : (
              "You"
            )}
          </span>

          {isAssistant && (
            <button
              onClick={handleCopy}
              className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-all text-xs flex items-center gap-1"
              title="Copy answer"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Markdown Render */}
        <div className="prose prose-invert prose-emerald text-sm text-zinc-200 max-w-none leading-relaxed prose-pre:bg-zinc-950 prose-pre:border prose-pre:border-zinc-800">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Citations Shelf */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="pt-2 border-t border-zinc-800/80">
            <span className="text-[11px] font-medium text-zinc-400 block mb-1.5 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-400" />
              Verified Sources ({message.citations.length})
            </span>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((c, idx) => (
                <CitationBadge
                  key={`${c.chunk_id}-${idx}`}
                  citation={c}
                  index={idx}
                  onClick={onSelectCitation}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
