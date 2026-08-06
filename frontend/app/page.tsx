"use client";

import { useState } from "react";

type Transaction = {
  id: number;
  merchant_raw: string;
  amount: number;
  category: string | null;
  date: string;
};

export default function Home() {
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  const userId = 1; // hardcoded for now, no auth yet

  async function addTransaction() {
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
    setTransactions((prev) => [...prev, data]);
    setMerchant("");
    setAmount("");
  }

  async function loadTransactions() {
    const res = await fetch(`http://localhost:8000/transactions/${userId}`);
    const data = await res.json();
    setTransactions(data);
  }

  return (
    <main className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">NeetiAi — transactions</h1>

      <div className="flex gap-2 mb-4">
        <input
          className="border p-2 flex-1"
          placeholder="merchant (e.g. SWIGGY ORDER 123)"
          value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
        />
        <input
          className="border p-2 w-28"
          placeholder="amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <button className="bg-black text-white px-4" onClick={addTransaction}>
          Add
        </button>
      </div>

      <button className="text-sm underline mb-4" onClick={loadTransactions}>
        Refresh list
      </button>

      <ul className="space-y-2">
        {transactions.map((tx) => (
          <li key={tx.id} className="border p-2 flex justify-between">
            <span>{tx.merchant_raw}</span>
            <span className="text-gray-500">{tx.category ?? "uncategorized"}</span>
            <span>₹{tx.amount}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}