import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, ShieldCheck, FileSearch, Database, ArrowRight } from "lucide-react";
import { Button } from "../components/ui/Button";
import { useAuth } from "../features/auth/AuthContext";

export const LandingPage: React.FC = () => {
  const { user, devLogin } = useAuth();
  const navigate = useNavigate();

  const handleDemoStart = () => {
    devLogin();
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-between selection:bg-emerald-500/20 selection:text-emerald-300">
      {/* Navigation */}
      <header className="h-20 border-b border-zinc-800/80 px-8 flex items-center justify-between max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-lg shadow-emerald-950">
            <Sparkles className="w-5 h-5" />
          </div>
          <span className="font-bold text-lg tracking-tight">Knowledge AI</span>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <Link to="/dashboard">
              <Button size="sm">Go to Dashboard</Button>
            </Link>
          ) : (
            <>
              <Button size="sm" variant="ghost" onClick={handleDemoStart}>
                Try Demo Instant
              </Button>
              <Link to="/auth">
                <Button size="sm">Sign In</Button>
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-5xl mx-auto px-6 py-20 text-center flex-1 flex flex-col items-center justify-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-8">
          <ShieldCheck className="w-3.5 h-3.5" /> Grounded Answers Over Fluent Guesses
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-zinc-100 max-w-3xl leading-tight">
          Precision Retrieval-Augmented Generation for Your Critical Documents.
        </h1>

        <p className="mt-6 text-base sm:text-lg text-zinc-400 max-w-2xl leading-relaxed">
          Upload PDFs, DOCX, TXT, and Markdown documents. Get answers strictly grounded in retrieved evidence, with verifiable source citations and honest abstention when evidence is absent.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center gap-4">
          <Link to="/auth">
            <Button size="lg" className="w-full sm:w-auto gap-2">
              Get Started <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Button size="lg" variant="secondary" onClick={handleDemoStart} className="w-full sm:w-auto">
            Explore Demo Mode
          </Button>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 text-left w-full">
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-4">
              <FileSearch className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-base text-zinc-100 mb-2">Verifiable Source Citations</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Every factual assertion cites the exact source document, page number, and section excerpt. Inspect sources directly in the side drawer.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center mb-4">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-base text-zinc-100 mb-2">Supabase pgvector Storage</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Chunk embeddings are persisted and indexed in PostgreSQL with pgvector HNSW indexing, enforcing strict user and collection data isolation.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-base text-zinc-100 mb-2">Honest Abstention</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              When documents do not contain sufficient evidence, the assistant honestly abstains instead of hallucinating plausibly-sounding guesses.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="h-16 border-t border-zinc-800/80 px-8 flex items-center justify-between text-xs text-zinc-500 max-w-7xl mx-auto w-full">
        <span>Knowledge AI — Week 6 AI Agent Development Roadmap</span>
        <span>Built with FastAPI, LangGraph & Supabase pgvector</span>
      </footer>
    </div>
  );
};
