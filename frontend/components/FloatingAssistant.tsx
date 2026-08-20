"use client";

import { useState } from "react";

export default function FloatingAssistant() {
  const [hovered, setHovered] = useState(false);

  return (
    <a
      href="/chat"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-3 group"
    >
      {hovered && (
        <span className="glass-solid px-4 py-2 rounded-full text-sm font-medium text-ink whitespace-nowrap
                          animate-[fadeIn_0.2s_ease-out]">
          Ask Kuber →
        </span>
      )}
      <div
        className="w-14 h-14 rounded-full bg-forest flex items-center justify-center
                   shadow-lg shadow-forest/30 hover:scale-110 active:scale-95
                   transition-transform duration-200 ease-out relative"
      >
        <span className="font-display text-2xl italic text-gold">क़</span>
        <span className="absolute inset-0 rounded-full border border-gold/40 animate-ping opacity-30" />
      </div>
    </a>
  );
}