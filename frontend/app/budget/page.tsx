"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import PageBackground from "@/components/PageBackground";
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

type IncomeSource = { id: number; label: string; amount: number; frequency: string };

const USER_ID = 1;

export default function BudgetPage() {
  const [savingsPct, setSavingsPct] = useState(15);
  const [result, setResult] = useState<BudgetResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [incomeSources, setIncomeSources] = useState<IncomeSource[]>([]);
  const [totalWeeklyIncome, setTotalWeeklyIncome] = useState<number | null>(null);
  const [newLabel, setNewLabel] = useState("");
  const [newAmount, setNewAmount] = useState("");
  const [newFrequency, setNewFrequency] = useState<"weekly" | "monthly">("weekly");
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

  async function loadIncome() {
  const res = await fetch(`http://localhost:8000/income-sources/${USER_ID}`);
  const data = await res.json();
  setIncomeSources(data.sources);
  setTotalWeeklyIncome(data.weekly_income);
}

async function addIncomeSource() {
  if (!newLabel || !newAmount) return;
  await fetch("http://localhost:8000/income-sources", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: USER_ID, label: newLabel, amount: parseFloat(newAmount), frequency: newFrequency }),
  });
  setNewLabel("");
  setNewAmount("");
  await loadIncome();
}

async function removeIncomeSource(id: number) {
  await fetch(`http://localhost:8000/income-sources/${id}`, { method: "DELETE" });
  await loadIncome();
}
useEffect(() => {
  loadIncome();
}, []);
  return (
    <main className="relative min-h-screen bg-paper pb-24 overflow-x-hidden">
  <PageBackground />
  <Nav />
  
      <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-12 space-y-8">
        <div>
          <p className="text-sm tracking-[0.15em] uppercase text-gold font-semibold mb-2">Budget</p>
          <h1 className="font-display text-4xl sm:text-5xl">
            How much do you want to <span className="italic text-forest">save</span>?
          </h1>
        </div>

                {/* Income sources */}
        <div className="glass rounded-3xl p-6 sm:p-8 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl text-forest">Your income</h2>
            {totalWeeklyIncome !== null && (
              <span className="font-mono text-sm ink-strong">₹{totalWeeklyIncome.toLocaleString()}/wk total</span>
            )}
          </div>

          {incomeSources.length > 0 && (
            <div className="space-y-2">
              {incomeSources.map((s) => (
                <div key={s.id} className="flex items-center justify-between text-sm p-3 rounded-xl bg-elevated/50">
                  <span>{s.label}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-ink-soft">₹{s.amount} / {s.frequency}</span>
                    <button onClick={() => removeIncomeSource(s.id)} className="text-rust text-xs hover:underline">
                      remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              className="flex-1 bg-elevated border border-hairline rounded-xl px-3 py-2.5 text-sm
                         placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50"
              placeholder="e.g. Weekend tutoring"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
            />
            <input
              className="sm:w-28 bg-elevated border border-hairline rounded-xl px-3 py-2.5 text-sm font-mono
                         placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50"
              placeholder="Amount"
              value={newAmount}
              onChange={(e) => setNewAmount(e.target.value)}
            />
            <select
              value={newFrequency}
              onChange={(e) => setNewFrequency(e.target.value as "weekly" | "monthly")}
              className="bg-elevated border border-hairline rounded-xl px-3 py-2.5 text-sm"
            >
              <option value="weekly">per week</option>
              <option value="monthly">per month</option>
            </select>
            <button
              onClick={addIncomeSource}
              className="px-5 py-2.5 bg-forest text-white rounded-xl text-sm font-medium
                         hover:bg-ink transition-colors duration-200 ease-out"
            >
              Add
            </button>
          </div>
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
            className="mt-6 w-full py-3.5 bg-forest text-gold rounded-2xl font-medium
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
