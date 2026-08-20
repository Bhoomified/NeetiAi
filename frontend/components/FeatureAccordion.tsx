"use client";

import { useState } from "react";

const FEATURES = [
  { title: "It sorts your spending", preview: "No manual categorizing, ever.", body: "Tell it what you bought — it figures out the category itself, learns from messy real transaction text." },
  { title: "It sees next week coming", preview: "Forecasts built on your real habits.", body: "Based on how you actually spend, not a generic template — trained specifically on student-style spending patterns." },
  { title: "It protects what matters", preview: "Fun money gets cut first, never rent.", body: "When money's tight, it prioritizes essentials automatically — your budget caps aren't a flat, unfair haircut." },
  { title: "It talks like a friend", preview: "Meet Kuber, your money bestie.", body: "Ask Kuber anything about your money. No jargon, no judgment, always grounded in your real numbers." },
  { title: "It knows the market", preview: "Live fund tracking, zero pressure.", body: "A risk quiz that actually makes sense, plus live mutual fund data — informational, never pushy." },
];

export default function FeatureAccordion() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="max-w-2xl mx-auto divide-y divide-hairline">
      {FEATURES.map((f, i) => (
        <div key={f.title} className="py-5">
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-start justify-between text-left group gap-4"
          >
            <div>
              <span className="font-display text-xl sm:text-2xl group-hover:text-forest transition-colors duration-200 ease-out block">
                {f.title}
              </span>
              <span className="text-xs text-gold uppercase tracking-wide mt-1 block">{f.preview}</span>
            </div>
            <svg
              className={`w-5 h-5 mt-1 shrink-0 text-forest transition-transform duration-300 ease-out ${open === i ? "rotate-180" : ""}`}
              viewBox="0 0 20 20" fill="none"
            >
              <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <div
            className={`grid transition-all duration-300 ease-out ${open === i ? "grid-rows-[1fr] opacity-100 mt-3" : "grid-rows-[0fr] opacity-0"}`}
          >
            <div className="overflow-hidden">
              <p className="text-ink-soft text-sm sm:text-base leading-relaxed pr-8">{f.body}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}