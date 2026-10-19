import React, { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useCollections } from "../../features/collections/CollectionContext";

export const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const {
    collections,
    selectedCollectionId,
    setSelectedCollectionId,
    conversations,
    activeConversationId,
    setActiveConversationId,
    deleteConversation,
  } = useCollections();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleSelectCollection = (id: string) => {
    setSelectedCollectionId(id);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    navigate("/chat");
  };

  const handleNewConversation = () => {
    setActiveConversationId(null);
    navigate("/chat");
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-zinc-950 text-zinc-100">
      <Navbar
        collections={collections}
        selectedCollectionId={selectedCollectionId}
        onSelectCollection={handleSelectCollection}
        onMenuToggle={() => setIsSidebarOpen((open) => !open)}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={deleteConversation}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        <main className="flex-1 min-w-0 overflow-y-auto bg-zinc-950/60 p-3 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
