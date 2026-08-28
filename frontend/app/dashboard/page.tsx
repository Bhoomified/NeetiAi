"use client";

import { useState, useEffect } from "react";
import Nav from "@/components/Nav";
import PageBackground from "@/components/PageBackground";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth-context";

type Transaction = {
  id: number;
  merchant_raw: string;
  amount: number;
  category: string | null;
  confidence_score: number | null;
  date: string;
};

type ForecastCategory = { category: string; predicted_amount: number; method: string };
type Forecast = {
  predicted_total: number;
  total_method: string;
  categories: ForecastCategory[];
};

type IncomeSource = { id: number; label: string; amount: number; frequency: string };

const LOW_CONFIDENCE = 0.6;

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const low = score < LOW_CONFIDENCE;
  return (
    <span
      className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${
        low ? "bg-rust/10 text-rust border border-rust/25" : "bg-forest/10 text-forest border border-forest/25"
      }`}
    >
      {low ? "review" : "✓"} {Math.round(score * 100)}%
    </span>
  );
}

export default function Dashboard() {
  const { backendUser } = useAuth();
  const USER_ID = backendUser?.id;

  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [loading, setLoading] = useState(false);

  // Income source state (moved from budget page)
  const [incomeSources, setIncomeSources] = useState<IncomeSource[]>([]);
  const [totalWeeklyIncome, setTotalWeeklyIncome] = useState<number | null>(null);
  const [newLabel, setNewLabel] = useState("");
  const [newAmount, setNewAmount] = useState("");
  const [newFrequency, setNewFrequency] = useState<"weekly" | "monthly">("weekly");

  async function loadAll() {
    try {
      const [txRes, fcRes] = await Promise.all([
        fetch(`http://localhost:8000/transactions/${USER_ID}`),
        fetch(`http://localhost:8000/forecast/${USER_ID}`),
      ]);

      if (!txRes.ok) {
        console.error("Transactions fetch failed:", txRes.status, await txRes.text());
        setTransactions([]);
      } else {
        const txData = await txRes.json();
        setTransactions(Array.isArray(txData) ? txData : []);
      }

      if (!fcRes.ok) {
        console.error("Forecast fetch failed:", fcRes.status, await fcRes.text());
        setForecast(null);
      } else {
        setForecast(await fcRes.json());
      }
    } catch (err) {
      console.error("Could not reach backend — is uvicorn running on :8000?", err);
      setTransactions([]);
      setForecast(null);
    }
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
    if (!USER_ID) return; // wait until the real backend user ID exists
    loadAll();
    loadIncome();
  }, [USER_ID]);

  async function addTransaction() {
    if (!merchant || !amount) return;
    setLoading(true);
    await fetch("http://localhost:8000/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER_ID, merchant_raw: merchant, amount: parseFloat(amount) }),
    });
    setMerchant("");
    setAmount("");
    await loadAll();
    setLoading(false);
  }

  return (
    <ProtectedRoute>
      <main className="relative min-h-screen bg-paper pb-24 overflow-x-hidden">
        <PageBackground />
        <Nav />

        <div className="max-w-5xl mx-auto px-6 sm:px-8 pt-12 space-y-8">
          <div>
            <p className="text-sm tracking-[0.15em] uppercase text-gold font-semibold mb-2">Dashboard</p>
            <h1 className="font-display text-4xl sm:text-5xl">
              Hey {backendUser?.name?.split(" ")[0] || "there"}, here's where your{" "}
              <span className="italic text-forest">money</span> went.
            </h1>
          </div>

          {/* Income sources (moved from budget page) */}
          <div className="glass rounded-3xl p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl text-forest">Your income</h2>
              {totalWeeklyIncome !== null && totalWeeklyIncome !== undefined && (
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

          {/* Add transaction */}
          <div className="glass rounded-3xl p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                className="flex-1 bg-elevated/80 border border-hairline rounded-2xl px-4 py-3.5 text-sm
                           placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50
                           transition-all duration-200 ease-out"
                placeholder="Merchant — e.g. SWIGGY ORDER 123"
                value={merchant}
                onChange={(e) => setMerchant(e.target.value)}
              />
              <input
                className="sm:w-32 bg-elevated/80 border border-hairline rounded-2xl px-4 py-3.5 text-sm font-mono
                           placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50
                           transition-all duration-200 ease-out"
                placeholder="Amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
              <button
                onClick={addTransaction}
                disabled={loading}
                className="px-6 py-3.5 bg-forest text-base rounded-2xl font-medium
                           hover:bg-ink transition-colors duration-200 ease-out disabled:opacity-50"
              >
                {loading ? "Adding…" : "Add"}
              </button>
            </div>
          </div>

          <div className="grid lg:grid-cols-5 gap-6">
            {/* Transaction list */}
            <div className="lg:col-span-3 space-y-3">
              <h2 className="font-display text-2xl text-forest mb-4">Recent transactions</h2>
              {transactions.length === 0 && (
                <div className="glass rounded-2xl p-8 text-center text-ink-soft text-sm">
                  No transactions yet — add one above.
                </div>
              )}
              {transactions.map((tx) => (
                <div
                  key={tx.id}
                  className="group flex items-center justify-between gap-4 p-4 rounded-2xl border border-hairline
                             bg-elevated/50 hover:border-gold hover:-translate-y-0.5
                             transition-all duration-200 ease-out"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{tx.merchant_raw}</p>
                    <p className="text-xs text-ink-soft capitalize mt-0.5">{tx.category ?? "uncategorized"}</p>
                  </div>
                  <ConfidenceBadge score={tx.confidence_score} />
                  <span className="font-mono text-sm ink-strong whitespace-nowrap">₹{tx.amount}</span>
                </div>
              ))}
            </div>

            {/* Forecast panel */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="font-display text-2xl text-forest mb-4">This week's forecast</h2>
              <div className="glass-forest rounded-3xl p-6 text-base">
                <p className="text-xs uppercase tracking-wide text-gold mb-2">Predicted total</p>
                <p className="font-display text-4xl mb-1">
                  ₹{forecast?.predicted_total?.toLocaleString() ?? "—"}
                </p>
                <p className="text-xs text-base/60">
                  {forecast?.total_method === "random_forest" ? "Model-based prediction" : "Based on recent average"}
                </p>
              </div>

              {forecast && forecast.categories.length > 0 && (
                <div className="glass rounded-3xl p-5 space-y-3">
                  {forecast.categories
                    .sort((a, b) => b.predicted_amount - a.predicted_amount)
                    .map((c) => (
                      <div key={c.category} className="flex items-center justify-between text-sm">
                        <span className="capitalize text-ink-soft">{c.category}</span>
                        <span className="font-mono ink-strong">₹{c.predicted_amount.toLocaleString()}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </ProtectedRoute>
  );
}