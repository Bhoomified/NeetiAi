"use client";

import { useEffect, useRef } from "react";

export default function FinanceLineArt() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const scrolled = window.scrollY;
      containerRef.current.querySelectorAll<HTMLElement>("[data-depth]").forEach((layer) => {
        const depth = parseFloat(layer.dataset.depth || "0.1");
        layer.style.transform = `translateY(${scrolled * depth}px)`;
      });
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div ref={containerRef} className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      {/* Piggy bank, upper right */}
      <svg data-depth="0.08" className="absolute right-[4%] top-28 w-52 h-52 opacity-[0.3] animate-drift-slow" viewBox="0 0 200 200" fill="none">
        <ellipse cx="100" cy="110" rx="70" ry="50" stroke="#183630" strokeWidth="1.8" />
        <path d="M60 75 Q 45 55, 55 45 Q 65 50, 65 65" stroke="#183630" strokeWidth="1.8" fill="none" />
        <circle cx="130" cy="100" r="6" fill="#C9A15E" />
        <rect x="85" y="60" width="30" height="6" rx="3" stroke="#6B2E2A" strokeWidth="1.5" />
        <line x1="100" y1="158" x2="100" y2="170" stroke="#183630" strokeWidth="1.8" />
        <line x1="70" y1="158" x2="70" y2="170" stroke="#183630" strokeWidth="1.8" />
      </svg>

      {/* Growth arrow zigzag, mid-left */}
      <svg data-depth="0.15" className="absolute left-[-3%] top-[35%] w-80 h-48 opacity-[0.28]" viewBox="0 0 300 160" fill="none">
        <path d="M10 140 L 70 60 L 120 100 L 180 30 L 240 70 L 290 15" stroke="#183630" strokeWidth="2" fill="none" strokeLinejoin="round" />
        <path d="M270 10 L 290 15 L 282 32" stroke="#183630" strokeWidth="2" fill="none" strokeLinejoin="round" />
        <circle cx="120" cy="100" r="3.5" fill="#C9A15E" />
        <circle cx="180" cy="30" r="3.5" fill="#C9A15E" />
      </svg>

      {/* Hands exchanging money, mid-right */}
      <svg data-depth="0.12" className="absolute right-[14%] top-[52%] w-40 h-40 opacity-[0.3] animate-drift" viewBox="0 0 200 200" fill="none">
        <path d="M40 60 L 90 90 L 95 100 Q 90 110, 80 105 L 40 80" stroke="#6B2E2A" strokeWidth="1.8" fill="none" />
        <path d="M160 140 L 110 110 L 105 100 Q 110 90, 120 95 L 160 120" stroke="#183630" strokeWidth="1.8" fill="none" />
        <rect x="85" y="85" width="45" height="28" rx="3" stroke="#C9A15E" strokeWidth="1.8" transform="rotate(15 100 100)" />
      </svg>

      {/* Receipt, lower left */}
      <svg data-depth="0.1" className="absolute left-[6%] bottom-[14%] w-32 h-40 opacity-[0.28] animate-drift-slow" viewBox="0 0 120 160" fill="none">
        <path d="M20 10 H100 V140 L90 150 L80 140 L70 150 L60 140 L50 150 L40 140 L30 150 L20 140 Z" stroke="#183630" strokeWidth="1.6" fill="none" />
        <line x1="35" y1="35" x2="85" y2="35" stroke="#6B2E2A" strokeWidth="1.4" />
        <line x1="35" y1="55" x2="85" y2="55" stroke="#6B2E2A" strokeWidth="1.4" />
        <line x1="35" y1="75" x2="70" y2="75" stroke="#6B2E2A" strokeWidth="1.4" />
        <text x="60" y="105" fontSize="20" fill="#C9A15E" textAnchor="middle">₹</text>
      </svg>

      {/* Coin stack, lower right */}
      <svg data-depth="0.1" className="absolute right-[8%] bottom-[8%] w-36 h-36 opacity-[0.3] animate-drift-slow" viewBox="0 0 150 150" fill="none">
        <ellipse cx="75" cy="120" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.6" />
        <ellipse cx="75" cy="105" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.6" />
        <ellipse cx="75" cy="90" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.6" />
        <ellipse cx="75" cy="75" rx="45" ry="12" stroke="#C9A15E" strokeWidth="1.6" />
      </svg>

      {/* Hourglass, top area */}
      <svg data-depth="0.06" className="absolute left-[42%] top-10 w-24 h-24 opacity-[0.25]" viewBox="0 0 200 200" fill="none">
        <path d="M60 30 L140 30 Q140 30 140 45 L100 100 L140 155 Q140 170 140 170 L60 170 Q60 170 60 155 L100 100 L60 45 Q60 30 60 30 Z"
          stroke="#183630" strokeWidth="1.8" strokeLinejoin="round" />
      </svg>

      {/* Wave line, bottom, flowing */}
      <svg data-depth="0.03" className="absolute bottom-0 left-0 w-[200%] h-24 opacity-[0.2] animate-wave" viewBox="0 0 1600 100" fill="none">
        <path d="M0 50 Q 100 10, 200 50 T 400 50 T 600 50 T 800 50 T 1000 50 T 1200 50 T 1400 50 T 1600 50"
          stroke="#183630" strokeWidth="1.6" fill="none" />
      </svg>
    </div>
  );
}