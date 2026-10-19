import React, { useRef, useEffect } from "react";
import { ArrowUp, CornerDownLeft } from "lucide-react";
import { Button } from "../ui/Button";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  disabled = false,
  placeholder = "Ask a question about your documents...",
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading && !disabled) {
        onSubmit();
      }
    }
  };

  return (
    <div className="relative rounded-2xl bg-zinc-900 border border-zinc-800 focus-within:border-emerald-500/60 focus-within:ring-2 focus-within:ring-emerald-500/20 shadow-lg shadow-black/30 transition-all p-2.5 sm:p-3">
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full resize-none bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none pr-14 leading-relaxed max-h-[180px]"
      />

      <div className="flex items-center justify-between pt-2 border-t border-zinc-800/60 text-xs text-zinc-400">
        <span className="text-[11px] flex items-center gap-1 text-zinc-400">
          <CornerDownLeft className="w-3 h-3 text-zinc-400" /> <span className="hidden sm:inline">Enter to send, Shift + Enter for new line</span><span className="sm:hidden">Enter to send</span>
        </span>

        <Button
          type="button"
          size="sm"
          onClick={onSubmit}
          disabled={!value.trim() || isLoading || disabled}
          isLoading={isLoading}
          className="h-8 w-8 p-0 rounded-lg shrink-0"
        >
          <ArrowUp className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
