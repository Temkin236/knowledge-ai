import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "../../types";
import { isSupabaseConfigured, supabase } from "../../lib/supabase";
import { setTokenGetter } from "../../api/client";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, displayName?: string) => Promise<void>;
  signOut: () => Promise<void>;
  devLogin: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "knowledge_ai_token";
const USER_KEY = "knowledge_ai_user";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem(USER_KEY);
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    setTokenGetter(() => token);
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  useEffect(() => {
    async function initAuth() {
      if (isSupabaseConfigured && supabase) {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session) {
            setToken(session.access_token);
            setUser({
              id: session.user.id,
              email: session.user.email,
              displayName: session.user.user_metadata?.display_name || session.user.email?.split("@")[0],
            });
          }
        } catch (err) {
          console.error("Error reading Supabase session:", err);
        }
      }
      setIsLoading(false);
    }
    initAuth();
  }, []);

  const signIn = async (email: string, password: string) => {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error("Supabase is not configured. Please use Demo Sign In or configure .env variables.");
    }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if (data.session) {
      setToken(data.session.access_token);
      setUser({
        id: data.user.id,
        email: data.user.email,
        displayName: data.user.user_metadata?.display_name || data.user.email?.split("@")[0],
      });
    }
  };

  const signUp = async (email: string, password: string, displayName?: string) => {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error("Supabase is not configured. Please use Demo Sign In or configure .env variables.");
    }
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { display_name: displayName || email.split("@")[0] },
      },
    });
    if (error) throw error;
    if (data.session && data.user) {
      setToken(data.session.access_token);
      setUser({
        id: data.user.id,
        email: data.user.email,
        displayName: displayName || data.user.email?.split("@")[0],
      });
    }
  };

  const signOut = async () => {
    if (isSupabaseConfigured && supabase) {
      await supabase.auth.signOut();
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const devLogin = () => {
    const devToken = "dev-token";
    const devUser: User = {
      id: "00000000-0000-0000-0000-000000000001",
      email: "dev@knowledge.ai",
      displayName: "Dev Engineer",
    };
    setToken(devToken);
    setUser(devUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        signIn,
        signUp,
        signOut,
        devLogin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
