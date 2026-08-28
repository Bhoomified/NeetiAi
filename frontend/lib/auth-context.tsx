"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Session } from "@supabase/supabase-js";

type BackendUser = { id: number; name: string; email: string; monthly_income: number };

type AuthContextType = {
  session: Session | null;
  backendUser: BackendUser | null;
  loading: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  session: null, backendUser: null, loading: true, signOut: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [backendUser, setBackendUser] = useState<BackendUser | null>(null);
  const [loading, setLoading] = useState(true);

  async function syncBackendUser(currentSession: Session) {
    const meta = currentSession.user.user_metadata;
    const res = await fetch("http://localhost:8000/users/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        supabase_uid: currentSession.user.id,
        email: currentSession.user.email,
        first_name: meta.first_name || meta.full_name?.split(" ")[0] || "there",
        last_name: meta.last_name || "",
      }),
    });
    if (res.ok) setBackendUser(await res.json());
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) syncBackendUser(session);
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) syncBackendUser(session);
      else setBackendUser(null);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  async function signOut() {
    await supabase.auth.signOut();
    setBackendUser(null);
  }

  return (
    <AuthContext.Provider value={{ session, backendUser, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);