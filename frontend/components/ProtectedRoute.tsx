"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !session) router.push("/login");
  }, [loading, session, router]);

  if (loading) {
    return <div className="min-h-screen bg-paper flex items-center justify-center text-ink-soft">Loading…</div>;
  }
  if (!session) return null;

  return <>{children}</>;
}