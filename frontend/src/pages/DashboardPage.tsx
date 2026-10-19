import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FolderPlus,
  FileText,
  MessageSquare,
  ArrowRight,
  Database,
  CheckCircle2,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { useCollections } from "../features/collections/CollectionContext";
import { api } from "../api/client";
import { formatDate } from "../lib/utils";

export const DashboardPage: React.FC = () => {
  const {
    collections,
    conversations,
    setSelectedCollectionId,
    refetchCollections,
  } = useCollections();
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newColName, setNewColName] = useState("");
  const [newColDesc, setNewColDesc] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const totalDocuments = collections.reduce((acc, c) => acc + (c.document_count || 0), 0);

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    setIsCreating(true);
    try {
      const col = await api.createCollection({
        name: newColName.trim(),
        description: newColDesc.trim() || undefined,
      });
      refetchCollections();
      setSelectedCollectionId(col.id);
      setIsModalOpen(false);
      setNewColName("");
      setNewColDesc("");
    } catch (err: any) {
      alert(err.message || "Failed to create collection.");
    } finally {
      setIsCreating(false);
    }
  };

  const handleOpenCollection = (id: string) => {
    setSelectedCollectionId(id);
    navigate("/knowledge-base");
  };

  const handleStartChatWithCollection = (id: string) => {
    setSelectedCollectionId(id);
    navigate("/chat");
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
            Welcome to Knowledge AI
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Grounded assistant powered by pgvector similarity search & LangGraph orchestration.
          </p>
        </div>

        <Button
          onClick={() => setIsModalOpen(true)}
          leftIcon={<FolderPlus className="w-4 h-4" />}
        >
          New Collection
        </Button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Total Collections</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-zinc-100 mt-2">{collections.length}</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Indexed Documents</span>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-zinc-100 mt-2">{totalDocuments}</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Conversations</span>
            <MessageSquare className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-zinc-100 mt-2">{conversations.length}</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Grounding Policy</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-sm font-semibold text-emerald-400 mt-3 flex items-center gap-1.5">
            Strict Citations Enforced
          </p>
        </Card>
      </div>

      {/* Collections Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-zinc-100">Knowledge Collections</h2>
          <Link to="/knowledge-base" className="text-xs text-emerald-400 hover:underline">
            Manage all
          </Link>
        </div>

        {collections.length === 0 ? (
          <div className="p-12 text-center border border-zinc-800 rounded-2xl bg-zinc-900/30">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
              <FolderPlus className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100">No collections created yet</h3>
            <p className="text-xs text-zinc-400 mt-1 max-w-sm mx-auto">
              Create your first knowledge collection to organize documents and start querying them.
            </p>
            <Button
              className="mt-6"
              size="sm"
              onClick={() => setIsModalOpen(true)}
            >
              Create First Collection
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {collections.map((col) => (
              <Card
                key={col.id}
                className="hover:border-zinc-700 transition-all cursor-pointer flex flex-col justify-between"
                onClick={() => handleOpenCollection(col.id)}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-sm text-zinc-100 truncate">{col.name}</h3>
                    <span className="text-[11px] font-mono text-zinc-400 bg-zinc-800/80 px-2 py-0.5 rounded">
                      {col.document_count} {col.document_count === 1 ? "doc" : "docs"}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 mt-2 line-clamp-2">
                    {col.description || "No description provided."}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-zinc-800 flex items-center justify-between text-xs">
                  <span className="text-zinc-500">{formatDate(col.created_at)}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartChatWithCollection(col.id);
                    }}
                    className="text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1"
                  >
                    Chat <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Modal: Create Collection */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Knowledge Collection"
        description="Organize your documents for semantically isolated retrieval."
      >
        <form onSubmit={handleCreateCollection} className="space-y-4">
          <Input
            label="Collection Name"
            placeholder="e.g. Q4 Financial Reports"
            value={newColName}
            onChange={(e) => setNewColName(e.target.value)}
            required
          />
          <Input
            label="Description (optional)"
            placeholder="e.g. Quarterly earnings statements and audits"
            value={newColDesc}
            onChange={(e) => setNewColDesc(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={isCreating}>
              Create Collection
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
