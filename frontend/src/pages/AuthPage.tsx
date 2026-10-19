import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, Shield, AlertCircle, ArrowRight } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useAuth } from "../features/auth/AuthContext";

export const AuthPage: React.FC = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { signIn, signUp, devLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isSignUp) {
        await signUp(email, password, displayName);
      } else {
        await signIn(email, password);
      }
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Authentication failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDevLogin = () => {
    devLogin();
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-6 selection:bg-emerald-500/20 selection:text-emerald-300">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center text-white shadow-xl shadow-emerald-950 mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-zinc-100">
            {isSignUp ? "Create Knowledge AI Account" : "Sign in to Knowledge AI"}
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Access your private, grounded document assistant
          </p>
        </div>

        {/* Card */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          {/* Quick Demo Mode Banner */}
          <div className="mb-6 p-4 rounded-xl bg-emerald-950/30 border border-emerald-900/50 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
              <Shield className="w-4 h-4" /> Quick Local Evaluation Mode
            </div>
            <p className="text-[11px] text-zinc-400 leading-normal">
              Skip cloud account setup to instantly test collections, document ingestion, and grounded chat.
            </p>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleDevLogin}
              className="mt-1 w-full text-xs text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10 justify-between"
            >
              <span>Continue with Instant Demo Login</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>

          <div className="relative my-6 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800"></div>
            </div>
            <span className="relative px-3 text-xs text-zinc-500 bg-zinc-900 uppercase tracking-wider font-mono">
              Or with credentials
            </span>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 p-3 text-xs text-red-400 bg-red-950/30 border border-red-900/50 rounded-xl">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <Input
                label="Full Name"
                placeholder="Ada Lovelace"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
              />
            )}

            <Input
              label="Email Address"
              type="email"
              placeholder="you@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" className="w-full" isLoading={isLoading}>
              {isSignUp ? "Sign Up" : "Sign In"}
            </Button>
          </form>

          {/* Toggle Tab */}
          <div className="mt-6 pt-4 border-t border-zinc-800/80 text-center text-xs text-zinc-400">
            {isSignUp ? (
              <span>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => setIsSignUp(false)}
                  className="text-emerald-400 hover:underline font-semibold"
                >
                  Sign In
                </button>
              </span>
            ) : (
              <span>
                Don't have an account yet?{" "}
                <button
                  type="button"
                  onClick={() => setIsSignUp(true)}
                  className="text-emerald-400 hover:underline font-semibold"
                >
                  Create Account
                </button>
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
