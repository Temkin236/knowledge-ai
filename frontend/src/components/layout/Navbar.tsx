import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, Database, LogOut, User, Menu } from "lucide-react";
import { useAuth } from "../../features/auth/AuthContext";
import { Collection } from "../../types";

interface NavbarProps {
  collections: Collection[];
  selectedCollectionId: string | null;
  onSelectCollection: (id: string) => void;
  onMenuToggle: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  collections,
  selectedCollectionId,
  onSelectCollection,
  onMenuToggle,
}) => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

  return (
    <header className="h-16 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md px-3 sm:px-6 flex items-center justify-between z-20 shrink-0">
      {/* Brand logo & mobile indicator */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuToggle}
          className="p-2 -ml-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <Link to="/dashboard" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-950">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-bold text-sm tracking-tight text-zinc-100 hidden sm:inline-block">
            Knowledge AI
          </span>
        </Link>
      </div>

      {/* Central Collection Selector */}
      <div className="flex items-center gap-2 max-w-md w-full justify-center mx-2">
        <div className="flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs min-w-0">
          <Database className="w-3.5 h-3.5 text-emerald-400 shrink-0 hidden sm:block" />
          <span className="text-zinc-400 shrink-0 hidden sm:inline">Collection:</span>
          {collections.length > 0 ? (
            <select
              value={selectedCollectionId || ""}
              onChange={(e) => onSelectCollection(e.target.value)}
              className="bg-transparent text-zinc-100 font-medium focus:outline-none cursor-pointer truncate max-w-[150px] sm:max-w-[200px]"
            >
              {collections.map((c) => (
                <option key={c.id} value={c.id} className="bg-zinc-900 text-zinc-100">
                  {c.name} ({c.document_count} docs)
                </option>
              ))}
            </select>
          ) : (
            <span className="text-zinc-500 italic">No collections</span>
          )}
        </div>
      </div>

      {/* User profile & actions */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-300">
          <User className="w-3.5 h-3.5 text-zinc-400" />
          <span className="truncate max-w-[120px]">{user?.displayName || user?.email || "User"}</span>
        </div>

        <button
          onClick={handleSignOut}
          className="p-2 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-zinc-900 transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
