"use client";

import { useState } from "react";

const FEATURES = [
  { title: "It sorts your spending", body: "Tell it what you bought — it figures out the category itself, no dropdowns to fill in." },
  { title: "It sees next week coming", body: "Based on how you actually spend, not a generic template." },
  { title: "It protects what matters", body: "When money's tight, it cuts fun stuff first — never your rent or fees." },
  { title: "It talks like a friend", body: "Ask Kuber anything about your money. No jargon, no judgment." },
  { title: "It knows the market", body: "Live fund tracking, a risk quiz that actually makes sense, zero pressure to invest." },
];

export default function FeatureAccordion() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="max-w-2xl mx-auto divide-y divide-hairline">
      {FEATURES.map((f, i) => (
        <div key={f.title} className="py-5">
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center justify-between text-left group"
          >
            <span className="font-display text-xl sm:text-2xl group-hover:text-forest transition-colors duration-200 ease-out">
              {f.title}
            </span>
            <span
              className={`text-gold text-2xl transition-transform duration-300 ease-out ${open === i ? "rotate-45" : ""}`}
            >
              +
            </span>
          </button>
          <div
            className={`grid transition-all duration-300 ease-out ${
              open === i ? "grid-rows-[1fr] opacity-100 mt-3" : "grid-rows-[0fr] opacity-0"
            }`}
            style={{ display: "grid" }}
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