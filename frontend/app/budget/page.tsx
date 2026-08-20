"use client";

import { useState } from "react";
import Nav from "@/components/Nav";

type Allocation = {
  category: string;
  predicted_amount: number;
  budget_cap: number;
  cut_percent: number;
};

type BudgetResult = {
  weekly_income: number;
  savings_target: number;
  projected_savings: number;
  target_met: boolean;
  allocations: Allocation[];
};

const USER_ID = 1;

export default function BudgetPage() {
  const [savingsPct, setSavingsPct] = useState(15);
  const [result, setResult] = useState<BudgetResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runOptimizer() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/budget/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, savings_target_pct: savingsPct / 100 }),
      });
      if (!res.ok) {
        const err = await res.json();
        setError(err.detail || "Could not build a budget.");
        setResult(null);
      } else {
        setResult(await res.json());
      }
    } catch (err) {
      setError("Could not reach backend — is uvicorn running?");
    }
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-base pb-24">
      <Nav />

      <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-12 space-y-8">
        <div>
          <p className="text-sm tracking-[0.15em] uppercase text-gold font-semibold mb-2">Budget</p>
          <h1 className="font-display text-4xl sm:text-5xl">
            How much do you want to <span className="italic text-forest">save</span>?
          </h1>
        </div>

        {/* Savings target slider */}
        <div className="glass rounded-3xl p-8">
          <div className="flex items-center justify-between mb-4">
            <label className="text-sm font-medium text-ink-soft">Weekly savings target</label>
            <span className="font-display text-3xl text-forest">{savingsPct}%</span>
          </div>
          <input
            type="range"
            min={5}
            max={60}
            step={5}
            value={savingsPct}
            onChange={(e) => setSavingsPct(parseInt(e.target.value))}
            className="w-full accent-forest"
          />
          <button
            onClick={runOptimizer}
            disabled={loading}
            className="mt-6 w-full py-3.5 bg-forest text-base rounded-2xl font-medium
                       hover:bg-ink transition-colors duration-200 ease-out disabled:opacity-50"
          >
            {loading ? "Calculating…" : "Build my budget"}
          </button>
        </div>

        {error && (
          <div className="glass rounded-2xl p-5 border border-rust/30 text-rust text-sm">{error}</div>
        )}

        {result && (
          <>
            {/* Summary */}
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="glass-forest rounded-3xl p-6 text-base">
                <p className="text-xs uppercase tracking-wide text-gold mb-2">Weekly income</p>
                <p className="font-display text-3xl">₹{result.weekly_income.toLocaleString()}</p>
              </div>
              <div className="glass rounded-3xl p-6">
                <p className="text-xs uppercase tracking-wide text-ink-soft mb-2">Savings target</p>
                <p className="font-display text-3xl text-forest">₹{result.savings_target.toLocaleString()}</p>
              </div>
              <div className={`rounded-3xl p-6 ${result.target_met ? "glass" : "glass border border-rust/30"}`}>
                <p className="text-xs uppercase tracking-wide text-ink-soft mb-2">Projected savings</p>
                <p className={`font-display text-3xl ${result.target_met ? "text-forest" : "text-rust"}`}>
                  ₹{result.projected_savings.toLocaleString()}
                </p>
                {!result.target_met && (
                  <p className="text-xs text-rust mt-1">Target not fully met at current spend</p>
                )}
              </div>
            </div>

            {/* Category allocations */}
            <div className="space-y-3">
              <h2 className="font-display text-2xl text-forest">Your budget, by category</h2>
              {result.allocations
                .sort((a, b) => b.cut_percent - a.cut_percent)
                .map((a) => (
                  <div key={a.category} className="glass rounded-2xl p-5">
                    <div className="flex items-center justify-between mb-2">
                      <span className="capitalize font-medium">{a.category}</span>
                      {a.cut_percent > 0 && (
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-rust/10 text-rust border border-rust/25">
                          −{a.cut_percent.toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-ink-soft line-through opacity-60">
                        ₹{a.predicted_amount.toLocaleString()}
                      </span>
                      <span className="text-sm">→</span>
                      <span className="font-mono ink-strong">₹{a.budget_cap.toLocaleString()}</span>
                    </div>
                    <div className="mt-3 h-1.5 bg-hairline rounded-full overflow-hidden">
                      <div
                        className="h-full bg-forest rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${(a.budget_cap / a.predicted_amount) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </>
        )}
      </div>
    </main>
  );
}