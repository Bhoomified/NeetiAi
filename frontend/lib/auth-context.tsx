"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { supabase } from "@/lib/supabase";
import { api, ApiError } from "@/lib/api";
import type { Session } from "@supabase/supabase-js";

type BackendUser = { id: number; name: string; email: string; monthly_income: number };
export type BackendStatus = "syncing" | "ok" | "unreachable";

type AuthContextType = {
  session: Session | null;
  backendUser: BackendUser | null;
  backendStatus: BackendStatus;
  loading: boolean;
  retrySync: () => void;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  session: null, backendUser: null, backendStatus: "syncing", loading: true,
  retrySync: () => {}, signOut: async () => {},
});

const RETRY_DELAYS_MS = [1000, 2000, 4000];
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [backendUser, setBackendUser] = useState<BackendUser | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("syncing");
  const [loading, setLoading] = useState(true);
  // getSession and onAuthStateChange both fire on load — share one in-flight sync per Supabase user
  const inFlight = useRef<{ uid: string; promise: Promise<void> } | null>(null);

  async function runSync(currentSession: Session) {
    const meta = currentSession.user.user_metadata;
    setBackendStatus("syncing");
    for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
      try {
        const user = await api<BackendUser>("/users/sync", {
          method: "POST",
          token: currentSession.access_token, // don't call supabase.auth inside its own callback
          json: {
            supabase_uid: currentSession.user.id,
            email: currentSession.user.email,
            first_name: meta.first_name || meta.full_name?.split(" ")[0] || "there",
            last_name: meta.last_name || "",
          },
        });
        setBackendUser(user);
        setBackendStatus("ok");
        return;
      } catch (err) {
        // 4xx won't fix itself on retry; network errors and 5xx (DB degraded) might
        if (err instanceof ApiError && err.status >= 400 && err.status < 500) break;
        if (attempt < RETRY_DELAYS_MS.length) await sleep(RETRY_DELAYS_MS[attempt]);
      }
    }
    setBackendStatus("unreachable");
    inFlight.current = null; // let retrySync / the next auth event try again
  }

  function syncBackendUser(currentSession: Session) {
    if (inFlight.current?.uid === currentSession.user.id) return inFlight.current.promise;
    const promise = runSync(currentSession);
    inFlight.current = { uid: currentSession.user.id, promise };
    return promise;
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
      else {
        inFlight.current = null;
        setBackendUser(null);
      }
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  function retrySync() {
    if (session) syncBackendUser(session);
  }

  async function signOut() {
    await supabase.auth.signOut();
    inFlight.current = null;
    setBackendUser(null);
  }

  return (
    <AuthContext.Provider value={{ session, backendUser, backendStatus, loading, retrySync, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
