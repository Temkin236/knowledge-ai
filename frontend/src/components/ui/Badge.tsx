import React from "react";
import { cn } from "../../lib/utils";
import { DocumentStatus } from "../../types";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: DocumentStatus | "SUCCESS" | "WARNING" | "INFO";
  variant?: "default" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({
  status = "INFO",
  variant = "default",
  className,
  children,
  ...props
}) => {
  const getColors = () => {
    switch (status) {
      case "INDEXED":
      case "SUCCESS":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "EMBEDDING":
      case "CHUNKING":
      case "EXTRACTING":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse";
      case "PENDING":
        return "bg-zinc-500/10 text-zinc-400 border-zinc-500/20";
      case "FAILED":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      default:
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    }
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border tracking-wide",
        getColors(),
        className
      )}
      {...props}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {children || status}
    </span>
  );
};
