import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  MessageSquare,
  Settings,
  Plus,
  Trash2,
} from "lucide-react";
import { Button } from "../ui/Button";
import { Conversation } from "../../types";
import { cn } from "../../lib/utils";

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isOpen,
  onClose,
}) => {
  const navItems = [
    { label: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
    { label: "Knowledge Base", icon: FolderKanban, path: "/knowledge-base" },
    { label: "Chat Assistant", icon: MessageSquare, path: "/chat" },
    { label: "Settings", icon: Settings, path: "/settings" },
  ];

  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
        />
      )}
    <aside className={cn(
      "fixed inset-y-0 left-0 top-16 z-40 w-72 border-r border-zinc-800 bg-zinc-950 flex flex-col justify-between h-[calc(100vh-4rem)] shrink-0 transition-transform lg:static lg:z-auto lg:w-64 lg:translate-x-0",
      isOpen ? "translate-x-0" : "-translate-x-full"
    )}>
      <div className="p-4 space-y-6 flex-1 overflow-hidden flex flex-col">
        {/* Main Navigation Links */}
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-colors",
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                )
              }
            >
              <item.icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Conversations History Section */}
        <div className="flex-1 flex flex-col min-h-0 pt-4 border-t border-zinc-800/80">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">
              Recent Chats
            </span>
            <Button
              size="sm"
              variant="ghost"
              onClick={onNewConversation}
              className="h-6 w-6 p-0 text-zinc-400 hover:text-zinc-100"
              title="Start New Chat"
            >
              <Plus className="w-3.5 h-3.5" />
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {conversations.length === 0 ? (
              <p className="text-xs text-zinc-600 italic px-2 py-3">No conversations yet.</p>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => { onSelectConversation(conv.id); onClose(); }}
                  className={cn(
                    "group flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-colors cursor-pointer",
                    activeConversationId === conv.id
                      ? "bg-zinc-900 text-zinc-100 font-medium border border-zinc-800"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50"
                  )}
                >
                  <span className="truncate max-w-[150px]">{conv.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-opacity"
                    title="Delete conversation"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Bottom Status / Footer */}
      <div className="p-4 border-t border-zinc-800/80 text-[11px] text-zinc-500 flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
          RAG Engine Ready
        </span>
        <span className="font-mono text-[10px]">v0.1.0</span>
      </div>
    </aside>
    </>
  );
};
