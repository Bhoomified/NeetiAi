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
      {/* Ambient contrast blob — forest green wash, upper right, gives the "movable stack" scene a base */}
      <div
        data-depth="0.06"
        className="absolute -right-32 -top-20 w-[32rem] h-[32rem] rounded-full opacity-[0.07] animate-drift-slow"
        style={{ background: "radial-gradient(circle, #183630 0%, transparent 70%)" }}
      />
      <div
        data-depth="0.1"
        className="absolute -left-40 top-[30%] w-[28rem] h-[28rem] rounded-full opacity-[0.06] animate-drift"
        style={{ background: "radial-gradient(circle, #C9A15E 0%, transparent 70%)" }}
      />

      {/* Hourglass echo, upper right */}
      <svg data-depth="0.08" className="absolute right-[6%] top-24 w-56 h-56 opacity-[0.16] animate-drift-slow" viewBox="0 0 200 200" fill="none">
        <path d="M60 30 L140 30 Q140 30 140 45 L100 100 L140 155 Q140 170 140 170 L60 170 Q60 170 60 155 L100 100 L60 45 Q60 30 60 30 Z"
          stroke="#C9A15E" strokeWidth="1.5" strokeLinejoin="round" />
      </svg>

      {/* Growth curve, mid-left */}
      <svg data-depth="0.15" className="absolute left-[-4%] top-[38%] w-96 h-64 opacity-[0.14]" viewBox="0 0 400 200" fill="none">
        <path d="M10 170 C 60 160, 90 150, 120 130 S 180 90, 220 95 S 280 60, 320 40 S 370 15, 390 10"
          stroke="#183630" strokeWidth="2" strokeLinecap="round" fill="none" />
        <circle cx="390" cy="10" r="3" fill="#C9A15E" />
      </svg>

      {/* Floating winged money note — signature element */}
      <svg data-depth="0.12" className="absolute right-[18%] top-[55%] w-40 h-40 opacity-[0.15] animate-drift" viewBox="0 0 200 200" fill="none">
        <rect x="60" y="70" width="90" height="55" rx="4" stroke="#6B2E2A" strokeWidth="1.5" />
        <circle cx="105" cy="97" r="14" stroke="#6B2E2A" strokeWidth="1.2" />
        <path d="M60 85 Q 30 75, 15 55 Q 10 45, 20 48 Q 40 55, 60 85" stroke="#C9A15E" strokeWidth="1.3" fill="none" />
        <path d="M150 85 Q 180 75, 195 55 Q 200 45, 190 48 Q 170 55, 150 85" stroke="#C9A15E" strokeWidth="1.3" fill="none" />
      </svg>

      {/* Coin stack, lower right */}
      <svg data-depth="0.1" className="absolute right-[8%] bottom-[8%] w-40 h-40 opacity-[0.14] animate-drift-slow" viewBox="0 0 150 150" fill="none">
        <ellipse cx="75" cy="120" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.5" />
        <ellipse cx="75" cy="105" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.5" />
        <ellipse cx="75" cy="90" rx="45" ry="12" stroke="#6B2E2A" strokeWidth="1.5" />
        <ellipse cx="75" cy="75" rx="45" ry="12" stroke="#C9A15E" strokeWidth="1.5" />
      </svg>

      {/* Second coin stack, upper-left, smaller */}
      <svg data-depth="0.14" className="absolute left-[10%] top-[12%] w-24 h-24 opacity-[0.13] animate-drift" viewBox="0 0 150 150" fill="none">
        <ellipse cx="75" cy="120" rx="35" ry="9" stroke="#183630" strokeWidth="1.3" />
        <ellipse cx="75" cy="107" rx="35" ry="9" stroke="#183630" strokeWidth="1.3" />
        <ellipse cx="75" cy="94" rx="35" ry="9" stroke="#C9A15E" strokeWidth="1.3" />
      </svg>

      {/* Free-hand flourish underline */}
      <svg data-depth="0.05" className="absolute left-[18%] top-[6%] w-48 h-16 opacity-[0.15]" viewBox="0 0 200 60" fill="none">
        <path d="M5 40 Q 50 5, 100 30 T 195 20" stroke="#C9A15E" strokeWidth="1.5" strokeLinecap="round" fill="none" />
      </svg>

      {/* Gentle wave line, bottom, drifting horizontally */}
      <svg
        data-depth="0.03"
        className="absolute bottom-0 left-0 w-[200%] h-24 opacity-[0.1] animate-wave"
        viewBox="0 0 1600 100" fill="none"
      >
        <path
          d="M0 50 Q 100 10, 200 50 T 400 50 T 600 50 T 800 50 T 1000 50 T 1200 50 T 1400 50 T 1600 50"
          stroke="#183630" strokeWidth="1.5" fill="none"
        />
      </svg>
    </div>
  );
}