"use client";

import { useState } from "react";

type Transaction = {
  id: number;
  merchant_raw: string;
  amount: number;
  category: string | null;
  confidence_score: number | null;
  date: string;
};

const LOW_CONFIDENCE_THRESHOLD = 0.6;

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span className="text-[11px] font-medium text-slate-400 bg-slate-100/80 dark:bg-slate-800/80 px-2.5 py-1 rounded-full backdrop-blur-sm">
        no score
      </span>
    );
  }

  const isLowConfidence = score < LOW_CONFIDENCE_THRESHOLD;
  const percent = Math.round(score * 100);

  return (
    <span
      className={`text-[11px] font-semibold px-3 py-1 rounded-full flex items-center gap-1 transition-transform hover:scale-105 ${
        isLowConfidence
          ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 shadow-sm shadow-amber-500/10"
          : "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 shadow-sm shadow-emerald-500/10"
      }`}
      title={isLowConfidence ? "Low confidence — might need manual correction" : "High confidence"}
    >
      <span className="text-xs">{isLowConfidence ? "⚠️" : "✨"}</span>
      <span>{percent}%</span>
    </span>
  );
}

export default function Home() {
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  const userId = 1; // hardcoded for now, no auth yet

  async function addTransaction() {
    if (!merchant || !amount) return;
    const res = await fetch("http://localhost:8000/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        merchant_raw: merchant,
        amount: parseFloat(amount),
      }),
    });
    const data = await res.json();
    setTransactions((prev) => [data, ...prev]);
    setMerchant("");
    setAmount("");
  }

  async function loadTransactions() {
    const res = await fetch(`http://localhost:8000/transactions/${userId}`);
    const data = await res.json();
    setTransactions(data);
  }

  const lowConfidenceCount = transactions.filter(
    (t) => t.confidence_score !== null && t.confidence_score < LOW_CONFIDENCE_THRESHOLD
  ).length;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 flex items-center justify-center font-sans antialiased relative overflow-hidden">
      {/* Background Ambient Glows */}
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 -right-32 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-xl relative z-10 space-y-6">
        {/* Header Section */}
        <header className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 p-6 rounded-3xl shadow-2xl">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
              NeetiAi
            </h1>
            <span className="text-xs font-semibold uppercase tracking-widest px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
              Live Beta
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <span>⚡</span> Categorized automatically by a trained model
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-purple-300 font-mono text-[10px]">
              XGBoost • F1 0.9459
            </span>
          </p>
        </header>

        {/* Input Form Card */}
        <section className="bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 p-4 rounded-3xl shadow-xl space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              className="bg-slate-950/80 border border-slate-800/80 p-3.5 flex-1 rounded-2xl text-sm placeholder:text-slate-500 text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-inner"
              placeholder="Merchant (e.g. SWIGGY ORDER 123)"
              value={merchant}
              onChange={(e) => setMerchant(e.target.value)}
            />
            <input
              className="bg-slate-950/80 border border-slate-800/80 p-3.5 w-full sm:w-28 rounded-2xl text-sm placeholder:text-slate-500 text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-inner font-mono"
              placeholder="Amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <button
              className="bg-gradient-to-r from-purple-500 via-pink-500 to-indigo-500 text-white font-semibold px-6 py-3.5 rounded-2xl hover:opacity-90 active:scale-95 transition-all shadow-lg shadow-purple-500/25 flex items-center justify-center gap-2"
              onClick={addTransaction}
            >
              <span>Add</span>
              <span className="text-xs">✨</span>
            </button>
          </div>
        </section>

        {/* List Controls & Notifications */}
        <div className="flex items-center justify-between px-2">
          <button
            className="text-xs font-semibold text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 hover:underline"
            onClick={loadTransactions}
          >
            <span>🔄</span> Refresh list
          </button>
          {lowConfidenceCount > 0 && (
            <span className="text-xs font-medium text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20 animate-pulse">
              ⚠️ {lowConfidenceCount} transaction{lowConfidenceCount > 1 ? "s" : ""} flagged for review
            </span>
          )}
        </div>

        {/* Transactions Feed */}
        <ul className="space-y-3">
          {transactions.length === 0 ? (
            <li className="bg-slate-900/40 backdrop-blur-md border border-slate-800/50 p-8 rounded-3xl text-center text-slate-500 text-sm">
              No transactions yet. Add one above or hit refresh!
            </li>
          ) : (
            transactions.map((tx) => (
              <li
                key={tx.id}
                className="group bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 hover:border-slate-700/80 p-4 rounded-2xl flex items-center justify-between gap-4 transition-all hover:translate-y-[-2px] hover:shadow-xl hover:shadow-purple-500/5"
              >
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="truncate text-sm font-semibold text-slate-200 group-hover:text-purple-200 transition-colors">
                    {tx.merchant_raw}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-block text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 capitalize">
                      🏷️ {tx.category ?? "uncategorized"}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <ConfidenceBadge score={tx.confidence_score} />
                  <span className="text-base font-bold font-mono text-slate-100 bg-slate-950/50 px-3 py-1.5 rounded-xl border border-slate-800/60">
                    ₹{tx.amount}
                  </span>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </main>
  );
}