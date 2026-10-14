"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const { session, backendUser, backendStatus, retrySync, signOut } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 120);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className="sticky top-0 z-50 glass">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
        <a href="/" className="font-display text-xl italic text-forest">NeetiAi</a>
        <div className="hidden sm:flex items-center gap-6 text-sm font-medium text-ink-soft overflow-x-auto">
          <a href="/" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Home</a>
          <a href="/dashboard" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Dashboard</a>
          <a href="/budget" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Budget</a>
          <a href="/chat" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Chat</a>
          <a href="/investments" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Investments</a>
        </div>

        {session ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-ink-soft hidden sm:inline">
              Hey, {backendUser?.name?.split(" ")[0] || "there"}
            </span>
            <button
              onClick={signOut}
              className="text-sm font-semibold px-5 py-2 rounded-full bg-forest text-white hover:bg-ink transition-colors duration-200 ease-out"
            >
              Log out
            </button>
          </div>
        ) : (
          <a
            href="/login"
            className="text-sm font-semibold px-5 py-2 rounded-full bg-forest text-white hover:bg-ink transition-colors duration-200 ease-out whitespace-nowrap"
          >
            Log in
          </a>
        )}
      </div>

      {session && backendStatus === "unreachable" && (
        <div role="status" className="border-t border-rust/30 bg-paper">
          <p className="max-w-6xl mx-auto px-6 sm:px-8 py-2 flex items-center gap-2 text-xs sm:text-sm text-rust">
            <span className="text-gold" aria-hidden>●</span>
            <span>Can&apos;t reach the NeetiAi server right now, so your numbers can&apos;t load.</span>
            <button
              onClick={retrySync}
              className="ml-auto font-semibold underline underline-offset-4 decoration-gold hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap"
            >
              Try again
            </button>
          </p>
        </div>
      )}

      <div
        className={`overflow-hidden transition-all duration-300 ease-out border-t border-hairline ${
          scrolled ? "max-h-12 opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <p className="text-center text-xs sm:text-sm tracking-[0.15em] uppercase text-ink-soft py-2">
          NeetiAi <span className="text-gold">·</span> The intelligence behind your finances.
        </p>
      </div>
    </nav>
  );
}