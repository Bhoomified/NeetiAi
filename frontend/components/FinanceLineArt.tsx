"use client";

import { useEffect, useRef } from "react";

export default function FinanceLineArt() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const scrolled = window.scrollY;
      const layers = containerRef.current.querySelectorAll<HTMLElement>("[data-depth]");
      layers.forEach((layer) => {
        const depth = parseFloat(layer.dataset.depth || "0.1");
        layer.style.transform = `translateY(${scrolled * depth}px)`;
      });
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div ref={containerRef} className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      {/* Hourglass echo of the brand mark, upper right */}
      <svg
        data-depth="0.08"
        className="absolute -right-10 top-20 w-64 h-64 opacity-[0.14]"
        viewBox="0 0 200 200" fill="none"
      >
        <path
          d="M60 30 L140 30 Q140 30 140 45 L100 100 L140 155 Q140 170 140 170 L60 170 Q60 170 60 155 L100 100 L60 45 Q60 30 60 30 Z"
          stroke="#C9A15E" strokeWidth="1.5" strokeLinejoin="round"
        />
      </svg>

      {/* Hand-drawn growth curve, mid-left */}
      <svg
        data-depth="0.15"
        className="absolute left-[-5%] top-[40%] w-96 h-64 opacity-[0.12]"
        viewBox="0 0 400 200" fill="none"
      >
        <path
          d="M10 170 C 60 160, 90 150, 120 130 S 180 90, 220 95 S 280 60, 320 40 S 370 15, 390 10"
          stroke="#183630" strokeWidth="2" strokeLinecap="round" fill="none"
        />
        <circle cx="390" cy="10" r="3" fill="#C9A15E" />
      </svg>

      {/* Coin stack sketch, lower right */}
      <svg
        data-depth="0.1"
        className="absolute right-[8%] bottom-[10%] w-40 h-40 opacity-[0.13]"
        viewBox="0 0 150 150" fill="none"
      >
        <ellipse cx="75" cy="120" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.5" />
        <ellipse cx="75" cy="105" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.5" />
        <ellipse cx="75" cy="90" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.5" />
        <ellipse cx="75" cy="75" rx="45" ry="12" stroke="#C9A15E" strokeWidth="1.5" />
      </svg>

      {/* Free-hand flourish underline, top-left */}
      <svg
        data-depth="0.05"
        className="absolute left-[15%] top-[8%] w-48 h-16 opacity-[0.15]"
        viewBox="0 0 200 60" fill="none"
      >
        <path
          d="M5 40 Q 50 5, 100 30 T 195 20"
          stroke="#C9A15E" strokeWidth="1.5" strokeLinecap="round" fill="none"
        />
      </svg>
    </div>
  );
}