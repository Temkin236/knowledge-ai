import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FolderKanban,
  Edit2,
  Trash2,
  Plus,
  RefreshCw,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { DocumentDropzone } from "../components/documents/DocumentDropzone";
import { DocumentTable } from "../components/documents/DocumentTable";
import { useCollections } from "../features/collections/CollectionContext";
import { api } from "../api/client";

export const KnowledgeBasePage: React.FC = () => {
  const {
    collections,
    selectedCollection,
    selectedCollectionId,
    setSelectedCollectionId,
    refetchCollections,
  } = useCollections();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [colName, setColName] = useState("");
  const [colDesc, setColDesc] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  // Load documents for active collection with auto-polling if any are processing
  const {
    data: documents = [],
    isLoading: isLoadingDocs,
    refetch: refetchDocs,
  } = useQuery({
    queryKey: ["documents", selectedCollectionId],
    queryFn: () => (selectedCollectionId ? api.getDocuments(selectedCollectionId) : Promise.resolve([])),
    enabled: !!selectedCollectionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (Array.isArray(data)) {
        const hasActive = data.some((d) =>
          ["PENDING", "EXTRACTING", "CHUNKING", "EMBEDDING"].includes(d.status)
        );
        return hasActive ? 2000 : false;
      }
      return false;
    },
  });

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!colName.trim()) return;
    try {
      const col = await api.createCollection({
        name: colName.trim(),
        description: colDesc.trim() || undefined,
      });
      await refetchCollections();
      setSelectedCollectionId(col.id);
      setIsCreateModalOpen(false);
      setColName("");
      setColDesc("");
    } catch (err: any) {
      alert(err.message || "Failed to create collection.");
    }
  };

  const handleUpdateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCollection || !colName.trim()) return;
    try {
      await api.updateCollection(selectedCollection.id, {
        name: colName.trim(),
        description: colDesc.trim() || undefined,
      });
      await refetchCollections();
      setIsEditModalOpen(false);
    } catch (err: any) {
      alert(err.message || "Failed to update collection.");
    }
  };

  const handleDeleteCollection = async () => {
    if (!selectedCollection) return;
    if (
      confirm(
        `Are you sure you want to delete '${selectedCollection.name}'? All documents and vector embeddings will be permanently removed.`
      )
    ) {
      await api.deleteCollection(selectedCollection.id);
      await refetchCollections();
      setSelectedCollectionId(null);
    }
  };

  const handleUploadDocument = async (file: File) => {
    if (!selectedCollectionId) return;
    setIsUploading(true);
    try {
      await api.uploadDocument(selectedCollectionId, file);
      await refetchDocs();
      await refetchCollections();
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    await api.deleteDocument(docId);
    await refetchDocs();
    await refetchCollections();
  };

  const handleRetryDocument = async (docId: string) => {
    await api.retryDocument(docId);
    await refetchDocs();
  };

  if (collections.length === 0) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 mx-auto">
          <FolderKanban className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-zinc-100">No Knowledge Collections</h2>
        <p className="text-xs text-zinc-400 max-w-sm mx-auto">
          You need at least one collection before uploading documents.
        </p>
        <Button onClick={() => setIsCreateModalOpen(true)}>Create Collection</Button>

        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Create Collection"
        >
          <form onSubmit={handleCreateCollection} className="space-y-4">
            <Input
              label="Collection Name"
              value={colName}
              onChange={(e) => setColName(e.target.value)}
              required
            />
            <Input
              label="Description (optional)"
              value={colDesc}
              onChange={(e) => setColDesc(e.target.value)}
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm">Create</Button>
            </div>
          </form>
        </Modal>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Header & Collection Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-zinc-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-zinc-100">
              {selectedCollection?.name || "Knowledge Base"}
            </h1>
            <button
              onClick={() => {
                if (selectedCollection) {
                  setColName(selectedCollection.name);
                  setColDesc(selectedCollection.description || "");
                  setIsEditModalOpen(true);
                }
              }}
              className="p-1 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
              title="Edit Collection"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDeleteCollection}
              className="p-1 rounded-md text-zinc-400 hover:text-red-400 hover:bg-red-950/20 transition-colors"
              title="Delete Collection"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            {selectedCollection?.description || "Upload and manage indexed documents in this collection."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetchDocs()}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => {
              setColName("");
              setColDesc("");
              setIsCreateModalOpen(true);
            }}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            New Collection
          </Button>
        </div>
      </div>

      {/* Upload Dropzone */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-zinc-200">Upload New Document</h2>
        <DocumentDropzone onUpload={handleUploadDocument} isUploading={isUploading} />
      </div>

      {/* Document Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-200">
            Indexed Documents ({documents.length})
          </h2>
          <span className="text-xs text-zinc-500 font-mono">
            {documents.reduce((acc, d) => acc + d.chunk_count, 0)} total chunks in pgvector
          </span>
        </div>
        <DocumentTable
          documents={documents}
          onDelete={handleDeleteDocument}
          onRetry={handleRetryDocument}
          isLoading={isLoadingDocs}
        />
      </div>

      {/* Modal: Create Collection */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Collection"
      >
        <form onSubmit={handleCreateCollection} className="space-y-4">
          <Input
            label="Collection Name"
            placeholder="e.g. Legal Contracts"
            value={colName}
            onChange={(e) => setColName(e.target.value)}
            required
          />
          <Input
            label="Description (optional)"
            placeholder="e.g. Master service agreements and NDAs"
            value={colDesc}
            onChange={(e) => setColDesc(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">Create</Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Collection */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Collection"
      >
        <form onSubmit={handleUpdateCollection} className="space-y-4">
          <Input
            label="Collection Name"
            value={colName}
            onChange={(e) => setColName(e.target.value)}
            required
          />
          <Input
            label="Description"
            value={colDesc}
            onChange={(e) => setColDesc(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">Save Changes</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
