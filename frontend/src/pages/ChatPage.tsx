import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  Database,
  Upload,
  AlertCircle,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatMessage } from "../components/chat/ChatMessage";
import { SourceDrawer } from "../components/citations/SourceDrawer";
import { useCollections } from "../features/collections/CollectionContext";
import { api } from "../api/client";
import { Citation } from "../types";

export const ChatPage: React.FC = () => {
  const queryClient = useQueryClient();
  const {
    selectedCollection,
    selectedCollectionId,
    activeConversationId,
    setActiveConversationId,
  } = useCollections();

  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingStage, setStreamingStage] = useState("");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load active conversation messages
  const { data: messages = [] } = useQuery({
    queryKey: ["messages", activeConversationId],
    queryFn: () =>
      activeConversationId
        ? api.getConversationMessages(activeConversationId)
        : Promise.resolve([]),
    enabled: !!activeConversationId,
  });

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  // Auto-open citation drawer if ?drawer=true is present in URL
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      window.location.search.includes("drawer=true") &&
      messages.length > 0 &&
      !selectedCitation
    ) {
      for (const m of messages) {
        if (m.citations && m.citations.length > 0) {
          setSelectedCitation(m.citations[0]);
          setIsDrawerOpen(true);
          break;
        }
      }
    }
  }, [messages, selectedCitation]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedCollectionId || isSending) return;

    const questionText = inputMessage.trim();
    setInputMessage("");
    setIsSending(true);

    try {
      await api.sendChatMessageStream({
        collection_id: selectedCollectionId,
        message: questionText,
        conversation_id: activeConversationId || undefined,
      }, (event) => {
        if (event.event === "status") setStreamingStage(event.stage || "Working");
        if (event.event === "delta") {
          setStreamingStage("Writing answer");
          setStreamingAnswer((answer) => answer + (event.delta || ""));
        }
        if (event.event === "done" && event.conversation_id) {
          setActiveConversationId(event.conversation_id);
          queryClient.invalidateQueries({ queryKey: ["messages", event.conversation_id] });
          queryClient.invalidateQueries({ queryKey: ["conversations"] });
        }
        if (event.event === "error") throw new Error(event.message || "Streaming failed.");
      });
    } catch (err: any) {
      alert(err.message || "Failed to send question.");
    } finally {
      setIsSending(false);
      setStreamingAnswer("");
      setStreamingStage("");
    }
  };

  const handleOpenCitation = (citation: Citation) => {
    setSelectedCitation(citation);
    setIsDrawerOpen(true);
  };

  if (!selectedCollection) {
    return (
      <div className="max-w-md mx-auto py-24 text-center space-y-4">
        <Database className="w-12 h-12 text-zinc-600 mx-auto" />
        <h3 className="text-lg font-semibold text-zinc-200">No Collection Selected</h3>
        <p className="text-xs text-zinc-400">
          Please select or create a knowledge collection to chat with your documents.
        </p>
        <Link to="/knowledge-base">
          <Button size="sm">Go to Knowledge Base</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0 max-w-4xl mx-auto">
      {/* Top Notice if Collection is Empty */}
      {selectedCollection.document_count === 0 && (
        <div className="mb-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
            <span>
              This collection has no indexed documents. Upload sources to receive grounded answers.
            </span>
          </div>
          <Link to="/knowledge-base">
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
            >
              <Upload className="w-3 h-3 mr-1" /> Upload
            </Button>
          </Link>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-4 pr-0 sm:pr-2 pb-4 sm:pb-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100">
              Chat with {selectedCollection.name}
            </h3>
            <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
              Ask questions about your uploaded documents. Every answer will be grounded in verified source excerpts with citations.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onSelectCitation={handleOpenCitation}
            />
          ))
        )}

        {isSending && (
          <div className="flex gap-3 sm:gap-4 px-3 sm:px-4 py-4 sm:py-5 rounded-2xl bg-zinc-900/40 border border-zinc-800/60">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="space-y-2 flex-1 min-w-0">
              <div className="text-xs text-emerald-400">{streamingStage || "Preparing retrieval"}</div>
              {streamingAnswer ? (
                <div className="text-sm text-zinc-200 whitespace-pre-wrap break-words">{streamingAnswer}</div>
              ) : (
                <>
                  <div className="h-4 bg-zinc-800 rounded w-1/2 animate-pulse" />
                  <div className="h-4 bg-zinc-800/60 rounded w-3/4 animate-pulse" />
                </>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="pt-2 shrink-0">
        <ChatInput
          value={inputMessage}
          onChange={setInputMessage}
          onSubmit={handleSendMessage}
          isLoading={isSending}
          disabled={selectedCollection.document_count === 0}
          placeholder={`Ask about ${selectedCollection.name}...`}
        />
      </div>

      {/* Citation Drawer */}
      <SourceDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        citation={selectedCitation}
      />
    </div>
  );
};
