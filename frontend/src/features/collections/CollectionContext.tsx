import React, { createContext, useContext, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Collection, Conversation } from "../../types";
import { useAuth } from "../auth/AuthContext";

interface CollectionContextType {
  collections: Collection[];
  selectedCollection: Collection | null;
  selectedCollectionId: string | null;
  setSelectedCollectionId: (id: string | null) => void;
  isLoadingCollections: boolean;
  refetchCollections: () => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  refetchConversations: () => void;
  deleteConversation: (id: string) => Promise<void>;
}

const CollectionContext = createContext<CollectionContextType | undefined>(undefined);

export const CollectionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Load collections
  const {
    data: collections = [],
    isLoading: isLoadingCollections,
    refetch: refetchCollections,
  } = useQuery({
    queryKey: ["collections", user?.id],
    queryFn: () => api.getCollections(),
    enabled: !!user,
  });

  // Select first collection automatically if none is selected
  useEffect(() => {
    if (collections.length > 0 && !selectedCollectionId) {
      setSelectedCollectionId(collections[0].id);
    }
  }, [collections, selectedCollectionId]);

  // Load conversations
  const {
    data: conversations = [],
    refetch: refetchConversations,
  } = useQuery({
    queryKey: ["conversations", user?.id],
    queryFn: () => api.getConversations(),
    enabled: !!user,
  });

  // Auto-select most recent conversation if none is active
  useEffect(() => {
    if (conversations.length > 0 && !activeConversationId) {
      setActiveConversationId(conversations[0].id);
    }
  }, [conversations, activeConversationId]);

  const selectedCollection =
    collections.find((c) => c.id === selectedCollectionId) || null;

  const deleteConversation = async (id: string) => {
    await api.deleteConversation(id);
    if (activeConversationId === id) {
      setActiveConversationId(null);
    }
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  };

  return (
    <CollectionContext.Provider
      value={{
        collections,
        selectedCollection,
        selectedCollectionId,
        setSelectedCollectionId,
        isLoadingCollections,
        refetchCollections,
        conversations,
        activeConversationId,
        setActiveConversationId,
        refetchConversations,
        deleteConversation,
      }}
    >
      {children}
    </CollectionContext.Provider>
  );
};

export const useCollections = () => {
  const context = useContext(CollectionContext);
  if (!context) {
    throw new Error("useCollections must be used within a CollectionProvider");
  }
  return context;
};
