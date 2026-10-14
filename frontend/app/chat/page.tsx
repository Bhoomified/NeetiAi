"use client";

import { useState, useRef, useEffect } from "react";
import Nav from "@/components/Nav";
import PageBackground from "@/components/PageBackground";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import StackedHeading from "@/components/StackedHeading";
import Marquee from "@/components/Marquee";

const SUGGESTIONS = [
  "How much did I spend this week?",
  "Where does most of my money go?",
  "How much on food this month?",
  "What will I spend next week?",
  "How much can I save?",
  "Help me budget for shopping",
  "Should I start a SIP?",
  "What's my income?",
  "What can you do?",
];

type Message = {
  role: "user" | "assistant";
  text: string;
  intent?: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Hello — I'm Kuber. Ask me about your spending, budget, savings or investments, or tap a suggestion below." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { backendUser } = useAuth();
  const USER_ID = backendUser?.id;

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text?: string) {
    const userMessage = (text ?? input).trim();
    if (!userMessage || loading) return;
    if (!USER_ID) {
      setMessages((prev) => [...prev, { role: "assistant", text: "still loading your account — one sec and try again" }]);
      return;
    }
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const data = await api<{ response: string; intent?: string }>("/chat", {
        method: "POST",
        json: { user_id: USER_ID, message: userMessage },
      });
      setMessages((prev) => [...prev, { role: "assistant", text: data.response, intent: data.intent }]);
    } catch (err) {
      const text = err instanceof ApiError && err.status !== 0 ? err.message : "couldn't reach the backend — try again?";
      setMessages((prev) => [...prev, { role: "assistant", text }]);
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
            <div className="text-center sm:text-left">
            <StackedHeading serif="Kuber" mono="Your money bestie, on call" align="left" />
            </div>
          </div>

          <div className="flex-1 glass rounded-3xl p-5 sm:p-6 overflow-y-auto space-y-4 mb-4 min-h-[400px] max-h-[55vh]">
            {messages.map((m, i) => (
              <div key={i} className={`msg-in flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-forest text-white rounded-br-sm"
                      : "bg-elevated border border-hairline rounded-bl-sm"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="msg-in bg-elevated border border-hairline px-4 py-4 rounded-2xl rounded-bl-sm flex gap-1.5" aria-label="Kuber is typing">
                  <span className="typing-dot" />
                  <span className="typing-dot" style={{ animationDelay: "0.15s" }} />
                  <span className="typing-dot" style={{ animationDelay: "0.3s" }} />
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>

          <Marquee speed={50} className="mb-4 -mx-2">
            {SUGGESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                disabled={loading}
                className="mx-1.5 whitespace-nowrap px-4 py-2 rounded-full border border-gold/50 bg-elevated/70
                           font-display italic text-sm text-forest hover:bg-forest hover:text-paper
                           transition-colors duration-200 ease-out disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </Marquee>

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
              onClick={() => sendMessage()}
              disabled={loading}
              className="px-6 py-3.5 bg-forest text-white rounded-2xl font-medium
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