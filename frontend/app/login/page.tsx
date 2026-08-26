"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit() {
    setLoading(true);
    setError(null);

    const { error } = isSignup
      ? await supabase.auth.signUp({ email, password })
      : await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError(error.message);
    } else {
      router.push("/dashboard");
    }
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-paper flex items-center justify-center px-6">
      <div className="glass rounded-3xl p-8 sm:p-10 max-w-md w-full space-y-5">
        <h1 className="font-display text-3xl text-center">
          {isSignup ? "Create your account" : "Welcome back"}
        </h1>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-elevated border border-hairline rounded-2xl px-4 py-3.5 text-sm
                     focus:outline-none focus:ring-2 focus:ring-gold/50"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-elevated border border-hairline rounded-2xl px-4 py-3.5 text-sm
                     focus:outline-none focus:ring-2 focus:ring-gold/50"
        />

        {error && <p className="text-rust text-sm">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-3.5 bg-forest text-white rounded-2xl font-medium
                     hover:bg-ink transition-colors duration-200 ease-out disabled:opacity-50"
        >
          {loading ? "…" : isSignup ? "Sign up" : "Log in"}
        </button>

        <button
          onClick={() => setIsSignup(!isSignup)}
          className="w-full text-center text-sm text-ink-soft hover:text-forest transition-colors duration-200 ease-out"
        >
          {isSignup ? "Already have an account? Log in" : "New here? Sign up"}
        </button>
      </div>
    </main>
  );
}