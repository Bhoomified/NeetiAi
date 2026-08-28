"use client";

import { useState, useRef, useEffect } from "react";
import Nav from "@/components/Nav";
import PageBackground from "@/components/PageBackground";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth-context";

type Message = {
  role: "user" | "assistant";
  text: string;
  intent?: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "heyyy 👋 ask me about your spending, budget, or investments" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { backendUser } = useAuth();
  const USER_ID = backendUser?.id;

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim()) return;
    if (!USER_ID) {
      setMessages((prev) => [...prev, { role: "assistant", text: "still loading your account — one sec and try again" }]);
      return;
    }
    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, message: userMessage }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.response, intent: data.intent }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", text: "couldn't reach the backend — try again?" }]);
    }
    setLoading(false);
  }

  return (
    <ProtectedRoute>
      <main className="relative min-h-screen bg-paper pb-24 overflow-x-hidden">
        <PageBackground />
        <Nav />

        <div className="max-w-2xl w-full mx-auto px-6 sm:px-8 pt-8 pb-4 flex-1 flex flex-col">
          <div>
            <p className="text-sm tracking-[0.15em] uppercase text-gold font-semibold mb-2">Chat</p>
            <h1 className="font-display text-3xl sm:text-4xl mb-6">
              Talk to <span className="italic text-forest">NeetiAi</span>.
            </h1>
          </div>

          <div className="flex-1 glass rounded-3xl p-5 sm:p-6 overflow-y-auto space-y-4 mb-4 min-h-[400px] max-h-[55vh]">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-forest text-base rounded-br-sm"
                      : "bg-elevated border border-hairline rounded-bl-sm"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-elevated border border-hairline px-4 py-3 rounded-2xl rounded-bl-sm text-sm text-ink-soft">
                  thinking…
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>

          <div className="flex gap-3 sticky bottom-4">
            <input
              className="flex-1 bg-elevated border border-hairline rounded-2xl px-5 py-3.5 text-sm
                         placeholder:text-ink-soft/60 focus:outline-none focus:ring-2 focus:ring-gold/50
                         transition-all duration-200 ease-out"
              placeholder="how much did I spend on food this week?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              className="px-6 py-3.5 bg-forest text-base rounded-2xl font-medium
                         hover:bg-ink transition-colors duration-200 ease-out disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </ProtectedRoute>
  );
}