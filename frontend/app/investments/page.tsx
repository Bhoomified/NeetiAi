"use client";

import { useState, useEffect } from "react";
import Nav from "@/components/Nav";

type Opportunity = {
  symbol: string;
  fund_name?: string;
  signal?: {
    latest_nav: number;
    recent_mean: number;
    z_score: number;
    is_opportunity: boolean;
    note: string;
  };
  error?: string;
};

type QuizState = {
  age: number;
  incomeStability: number;
  horizonMonths: number;
  lossReaction: number;
  savingsMonths: number;
};

type FundSearchResult = { schemeCode: number; schemeName: string };

const USER_ID = 1; // TODO: replace with logged-in user's real ID once auth is built

const INCOME_LABELS = ["Very unstable", "Unstable", "Somewhat stable", "Stable", "Very stable"];

function mapAgeToScore(age: number): number {
  if (age <= 25) return 5;
  if (age <= 35) return 4;
  if (age <= 45) return 3;
  if (age <= 60) return 2;
  return 1;
}

function mapHorizonToScore(months: number): number {
  if (months <= 6) return 1;
  if (months <= 18) return 2;
  if (months <= 36) return 3;
  if (months <= 60) return 4;
  return 5;
}

function mapSavingsToScore(months: number): number {
  if (months <= 3) return 1;
  if (months <= 8) return 2;
  if (months <= 15) return 3;
  if (months <= 22) return 4;
  return 5;
}

export default function InvestmentsPage() {
  const [quiz, setQuiz] = useState<QuizState>({
    age: 21, incomeStability: 3, horizonMonths: 12, lossReaction: 3, savingsMonths: 3,
  });
  const [riskProfile, setRiskProfile] = useState<string | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(false);

  // Search state — moved INSIDE the component, where all hooks must live
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<FundSearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  async function loadOpportunities() {
    const res = await fetch(`http://localhost:8000/investments/opportunities/${USER_ID}`);
    const data = await res.json();
    setOpportunities(data.opportunities || []);
  }

  useEffect(() => {
    loadOpportunities();
  }, []);

  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(`http://localhost:8000/investments/search?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(await res.json());
      } catch {
        setSearchResults([]);
      }
      setSearching(false);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  async function checkRiskProfile() {
    setLoading(true);
    const payload = {
      age_score: mapAgeToScore(quiz.age),
      income_stability: quiz.incomeStability,
      investment_horizon: mapHorizonToScore(quiz.horizonMonths),
      loss_reaction: quiz.lossReaction,
      existing_savings_months: mapSavingsToScore(quiz.savingsMonths),
    };
    const res = await fetch("http://localhost:8000/investments/risk-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    setRiskProfile(data.risk_profile);
    setLoading(false);
  }

  async function addFund(schemeCode: number) {
    await fetch("http://localhost:8000/investments/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER_ID, symbol: String(schemeCode) }),
    });
    setSearchQuery("");
    setSearchResults([]);
    await loadOpportunities();
  }

  return (
    <main className="min-h-screen bg-base pb-24">
      <Nav />

      <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-12 space-y-10">
        <div>
          <p className="text-sm tracking-[0.15em] uppercase text-gold font-semibold mb-2">Investments</p>
          <h1 className="font-display text-4xl sm:text-5xl">
            Know your <span className="italic text-forest">risk</span>, track your funds.
          </h1>
        </div>

        {/* Risk quiz */}
        <div className="glass rounded-3xl p-6 sm:p-8 space-y-7">
          <h2 className="font-display text-2xl text-forest">Risk profile quiz</h2>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-ink-soft">How old are you?</label>
              <span className="font-mono text-sm ink-strong">{quiz.age} yrs</span>
            </div>
            <input
              type="range" min={18} max={80} value={quiz.age}
              onChange={(e) => setQuiz((p) => ({ ...p, age: parseInt(e.target.value) }))}
              className="w-full accent-forest"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-ink-soft">How stable is your income right now?</label>
              <span className="font-mono text-sm ink-strong">{INCOME_LABELS[quiz.incomeStability - 1]}</span>
            </div>
            <input
              type="range" min={1} max={5} value={quiz.incomeStability}
              onChange={(e) => setQuiz((p) => ({ ...p, incomeStability: parseInt(e.target.value) }))}
              className="w-full accent-forest"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-ink-soft">How long before you'd need this money back?</label>
              <span className="font-mono text-sm ink-strong">
                {quiz.horizonMonths < 12 ? `${quiz.horizonMonths} mo` : `${(quiz.horizonMonths / 12).toFixed(1)} yr`}
              </span>
            </div>
            <input
              type="range" min={1} max={60} value={quiz.horizonMonths}
              onChange={(e) => setQuiz((p) => ({ ...p, horizonMonths: parseInt(e.target.value) }))}
              className="w-full accent-forest"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-ink-soft">
                If your investment dropped 10%, how calm would you stay?
              </label>
              <span className="font-mono text-sm ink-strong">{quiz.lossReaction} / 5</span>
            </div>
            <input
              type="range" min={1} max={5} value={quiz.lossReaction}
              onChange={(e) => setQuiz((p) => ({ ...p, lossReaction: parseInt(e.target.value) }))}
              className="w-full accent-forest"
            />
            <div className="flex justify-between text-[11px] text-ink-soft/70 mt-1">
              <span>Low — I'd panic</span>
              <span>High — I'd stay calm</span>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-ink-soft">How many months of expenses do you have saved?</label>
              <span className="font-mono text-sm ink-strong">{quiz.savingsMonths} mo</span>
            </div>
            <input
              type="range" min={1} max={30} value={quiz.savingsMonths}
              onChange={(e) => setQuiz((p) => ({ ...p, savingsMonths: parseInt(e.target.value) }))}
              className="w-full accent-forest"
            />
          </div>

          <button
            onClick={checkRiskProfile}
            disabled={loading}
            className="w-full py-3.5 bg-forest text-base rounded-2xl font-medium
                       hover:bg-ink transition-colors duration-200 ease-out disabled:opacity-50"
          >
            {loading ? "Calculating…" : "Find my risk profile"}
          </button>
          {riskProfile && (
            <div className="glass-forest rounded-2xl p-5 text-base text-center">
              <p className="text-xs uppercase tracking-wide text-gold mb-1">Your risk profile</p>
              <p className="font-display text-2xl capitalize">{riskProfile}</p>
            </div>
          )}
        </div>

        {/* Watchlist */}
        <div className="space-y-4">
          <h2 className="font-display text-2xl text-forest">Fund watchlist</h2>

          <div className="relative">
            <input
              className="w-full bg-elevated border border-hairline rounded-2xl px-4 py-3.5 text-sm
                         placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50
                         transition-all duration-200 ease-out"
              placeholder="Search a fund — e.g. Axis Bluechip, HDFC Flexi Cap…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searching && (
              <p className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-ink-soft">searching…</p>
            )}
            {searchResults.length > 0 && (
              <div className="absolute z-10 w-full mt-2 glass rounded-2xl overflow-hidden shadow-lg max-h-72 overflow-y-auto">
                {searchResults.map((r) => (
                  <button
                    key={r.schemeCode}
                    onClick={() => addFund(r.schemeCode)}
                    className="w-full text-left px-4 py-3 text-sm hover:bg-forest/5
                               transition-colors duration-150 ease-out border-b border-hairline last:border-0"
                  >
                    {r.schemeName}
                  </button>
                ))}
              </div>
            )}
          </div>

          {opportunities.length === 0 && (
            <div className="glass rounded-2xl p-8 text-center text-ink-soft text-sm">
              No funds tracked yet — search and add one above.
            </div>
          )}

          {opportunities.map((o, i) => (
            <div key={`${o.symbol}-${i}`} className="glass rounded-2xl p-5">
              {o.error ? (
                <p className="text-sm text-rust">{o.symbol} — {o.error}</p>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">{o.fund_name}</p>
                    {o.signal?.is_opportunity && (
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-forest/10 text-forest border border-forest/25">
                        signal
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-ink-soft">
                    <span className="font-mono ink-strong">NAV: ₹{o.signal?.latest_nav}</span>
                    <span>Avg: ₹{o.signal?.recent_mean}</span>
                    <span>z: {o.signal?.z_score}</span>
                  </div>
                  <p className="text-xs text-ink-soft/70 mt-2 italic">{o.signal?.note}</p>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}