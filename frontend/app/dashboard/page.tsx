"use client";

import { useState, useEffect } from "react";
import Nav from "@/components/Nav";
import PageBackground from "@/components/PageBackground";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth-context";
import StackedHeading from "@/components/StackedHeading";

type Transaction = {
  id: number;
  merchant_raw: string;
  amount: number;
  category: string | null;
  confidence_score: number | null;
  date: string;
};

type Explanation = {
  category: string | null;
  confidence: number | null;
  method: string;
  contributors: { feature: string; contribution: number; is_amount: boolean }[];
  note?: string;
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
  const [newFrequency, setNewFrequency] = useState<"weekly" | "monthly" | "one_time">("weekly");
  const [explainingId, setExplainingId] = useState<number | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
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

    async function explainTransaction(txId: number) {
    if (explainingId === txId) {
      setExplainingId(null);
      setExplanation(null);
      return;
    }
    setExplainingId(txId);
    setExplanation(null);
    try {
      const res = await fetch(`http://localhost:8000/transactions/${txId}/explain`);
      if (res.ok) setExplanation(await res.json());
    } catch {
      setExplanation(null);
    }
  }
  
  return (
    <ProtectedRoute>
      <main className="relative min-h-screen bg-paper pb-24 overflow-x-hidden">
        <PageBackground />
        <Nav />

        <div className="max-w-5xl mx-auto px-6 sm:px-8 pt-12 space-y-8">
          <div>
            <div className="text-center sm:text-left">
      <StackedHeading
          serif={`Hey ${backendUser?.name?.split(" ")[0] || "there"}`}
          mono="Here's where your money went"
          align="left"
              />
          </div>
          </div>

          {/* Income sources (moved from budget page) */}
          <div className="glass rounded-3xl p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl text-forest">Your income</h2>
              {totalWeeklyIncome !== null && (
                <span className="tabular text-sm ink-strong">₹{totalWeeklyIncome.toLocaleString()}/wk total</span>
                )}
            </div>

            {incomeSources.length > 0 && (
              <div className="space-y-2">
                {incomeSources.map((s) => (
                  <div key={s.id} className="flex items-center justify-between text-sm p-3 rounded-xl bg-elevated/50">
                    <span>{s.label}</span>
                    <div className="flex items-center gap-3">
                        <span className="tabular text-ink-soft">
                          ₹{s.amount} {s.frequency === "one_time" ? "· one-time" : `/ ${s.frequency}`}
                        </span>
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
                className="sm:w-28 bg-elevated border border-hairline rounded-xl px-3 py-2.5 text-sm tabular
                           placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50"
                placeholder="Amount"
                value={newAmount}
                onChange={(e) => setNewAmount(e.target.value)}
              />
              <select
                value={newFrequency}
                onChange={(e) => setNewFrequency(e.target.value as "weekly" | "monthly" | "one_time")}
                className="bg-elevated border border-hairline rounded-xl px-3 py-2.5 text-sm"
              >
                <option value="weekly">per week</option>
                <option value="monthly">per month</option>
                <option value="one_time">one-time</option>
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
                className="sm:w-32 bg-elevated/80 border border-hairline rounded-2xl px-4 py-3.5 text-sm tabular
                           placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50
                           transition-all duration-200 ease-out"
                placeholder="Amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
              <button
                onClick={addTransaction}
                disabled={loading}
                className="px-6 py-3.5 bg-forest text-white rounded-2xl font-medium
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
          <div key={tx.id} className="space-y-2">
            <button
              onClick={() => explainTransaction(tx.id)}
              className="w-full group flex items-center justify-between gap-4 p-4 rounded-2xl border border-hairline
                        bg-elevated/50 hover:border-gold hover:-translate-y-0.5
                        transition-all duration-200 ease-out text-left"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{tx.merchant_raw}</p>
                <p className="text-xs text-ink-soft capitalize mt-0.5">
                  {tx.category ?? "uncategorized"}
                  <span className="text-gold ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    why?
                  </span>
                </p>
              </div>
              <ConfidenceBadge score={tx.confidence_score} />
              <span className="tabular text-sm ink-strong whitespace-nowrap">₹{tx.amount}</span>
            </button>

            {explainingId === tx.id && (
              <div className="glass-solid rounded-2xl p-4 text-sm space-y-3">
                {!explanation ? (
                  <p className="text-ink-soft text-xs">Working out why…</p>
                ) : (
                  <>
                    <p className="text-xs text-ink-soft">
                      Sorted as <span className="ink-strong capitalize">{explanation.category}</span> because of:
                    </p>
                    <div className="space-y-2">
                      {explanation.contributors.map((c, i) => {
                        const maxAbs = Math.max(...explanation.contributors.map((x) => Math.abs(x.contribution)), 0.0001);
                        const width = (Math.abs(c.contribution) / maxAbs) * 100;
                        const positive = c.contribution >= 0;
                        return (
                          <div key={i}>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="tabular">
                                {c.is_amount ? `the amount (₹${tx.amount})` : `"${c.feature.trim()}"`}
                              </span>
                              <span className={positive ? "text-forest" : "text-rust"}>
                                {positive ? "supports" : "argues against"}
                              </span>
                            </div>
                            <div className="h-1.5 bg-hairline/50 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ease-out ${
                                  positive ? "bg-forest" : "bg-rust"
                                }`}
                                style={{ width: `${width}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    {explanation.method !== "shap" && (
                      <p className="text-[10px] text-ink-soft/70 italic">
                        Approximate explanation — exact attribution unavailable for this one.
                      </p>
                    )}
                  </>
                )}
              </div>
            )}
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
                        <span className="tabular ink-strong">₹{c.predicted_amount.toLocaleString()}</span>
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