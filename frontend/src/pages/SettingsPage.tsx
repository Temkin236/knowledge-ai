import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  User,
  Cpu,
  Database,
  LogOut,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { useAuth } from "../features/auth/AuthContext";
import { api } from "../api/client";

export const SettingsPage: React.FC = () => {
  const { user, signOut } = useAuth();

  const { data: readyData } = useQuery({
    queryKey: ["readyStatus"],
    queryFn: () => api.getReady(),
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="pb-4 border-b border-zinc-800">
        <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>
        <p className="text-xs text-zinc-400 mt-1">
          System telemetry, model configurations, and profile details.
        </p>
      </div>

      {/* User Profile Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-4 h-4 text-emerald-400" /> Account Profile
          </CardTitle>
        </CardHeader>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-zinc-500 block mb-1">User Identifier (UUID)</span>
            <span className="font-mono text-zinc-300 bg-zinc-950 px-2 py-1 rounded border border-zinc-800 block truncate">
              {user?.id || "N/A"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block mb-1">Email Address</span>
            <span className="font-mono text-zinc-300 bg-zinc-950 px-2 py-1 rounded border border-zinc-800 block truncate">
              {user?.email || "dev@knowledge.ai"}
            </span>
          </div>
        </div>
      </Card>

      {/* AI & Vector Architecture Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-400" /> RAG & Model Configuration
          </CardTitle>
        </CardHeader>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800">
            <span className="text-zinc-500 block">Generation Model</span>
            <span className="font-semibold text-zinc-200 mt-1 block">
              Google Gemini 2.5 Flash
            </span>
          </div>
          <div className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800">
            <span className="text-zinc-500 block">Embedding Model</span>
            <span className="font-semibold text-zinc-200 mt-1 block">
              Google text-embedding-004 (768 Dimensions)
            </span>
          </div>
          <div className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800">
            <span className="text-zinc-500 block">Retrieval Strategy</span>
            <span className="font-semibold text-zinc-200 mt-1 block">
              Cosine Similarity (Top-K: 5, Threshold: 0.30)
            </span>
          </div>
          <div className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800">
            <span className="text-zinc-500 block">Orchestration Graph</span>
            <span className="font-semibold text-zinc-200 mt-1 block">
              LangGraph StateGraph with Grounding Validation
            </span>
          </div>
        </div>
      </Card>

      {/* System Health Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-400" /> Backend Infrastructure
          </CardTitle>
        </CardHeader>
        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-950/60 border border-zinc-800">
            <span className="font-medium text-zinc-300">Database & pgvector Connection</span>
            {readyData?.checks?.database === "connected" ? (
              <span className="text-emerald-400 flex items-center gap-1 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            ) : (
              <span className="text-amber-400 flex items-center gap-1 font-mono">
                <AlertCircle className="w-3.5 h-3.5" /> Checking...
              </span>
            )}
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-950/60 border border-zinc-800">
            <span className="font-medium text-zinc-300">Model Provider Integration</span>
            <span className="text-emerald-400 flex items-center gap-1 font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" /> {readyData?.checks?.gemini_api || "Active"}
            </span>
          </div>
        </div>
      </Card>

      {/* Sign Out Card */}
      <Card className="border-red-900/30 bg-red-950/10">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-zinc-200">End Session</h4>
            <p className="text-xs text-zinc-400 mt-0.5">
              Sign out and clear local session credentials.
            </p>
          </div>
          <Button variant="danger" size="sm" onClick={() => signOut()}>
            <LogOut className="w-3.5 h-3.5 mr-1.5" /> Sign Out
          </Button>
        </div>
      </Card>
    </div>
  );
};
