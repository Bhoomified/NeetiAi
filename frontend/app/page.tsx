import Nav from "@/components/Nav";
import FinanceLineArt from "@/components/FinanceLineArt";
import MagneticButton from "@/components/MagneticButton";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <FinanceLineArt />
      <Nav />

      {/* Hero */}
      <section className="relative max-w-4xl mx-auto px-6 sm:px-8 pt-20 sm:pt-32 pb-24 text-center">
        <p className="text-sm tracking-[0.2em] uppercase text-gold font-semibold mb-6">
          Built from scratch, for students
        </p>
        <h1 className="font-display text-5xl sm:text-7xl leading-[1.05] mb-6">
          Your money,<br />
          <span className="italic text-forest">finally </span>
          <span className="ink-strong">understood.</span>
        </h1>
        <p className="text-lg text-ink-soft max-w-xl mx-auto mb-10 leading-relaxed">
          NeetiAi learns how you actually spend, forecasts what's next, and talks
          about it like a friend who happens to be good with money — not a spreadsheet.
        </p>
        <div className="flex items-center justify-center gap-4">
          <MagneticButton>Start tracking →</MagneticButton>
        </div>
      </section>

      {/* Signature: live-feeling stat strip */}
      <section className="relative max-w-5xl mx-auto px-6 sm:px-8 pb-24">
        <div className="glass rounded-3xl p-8 sm:p-12 grid grid-cols-2 sm:grid-cols-4 gap-8">
          {[
            { label: "Categorization accuracy", value: "94.6%" },
            { label: "Forecast improvement", value: "26–33%" },
            { label: "Models trained from scratch", value: "5" },
            { label: "Built for", value: "students" },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="font-display text-3xl sm:text-4xl text-forest mb-1">{stat.value}</p>
              <p className="text-xs text-ink-soft uppercase tracking-wide">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative max-w-6xl mx-auto px-6 sm:px-8 pb-32">
        <h2 className="font-display text-3xl sm:text-4xl mb-12 text-center">
          What it actually does
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { title: "Categorizes automatically", desc: "Reads messy, real transaction text — no manual sorting." },
            { title: "Forecasts your week", desc: "Weekly spend predictions, trained on real behavioral patterns." },
            { title: "Budgets that protect what matters", desc: "Cuts discretionary spend first, never touches essentials unfairly." },
            { title: "Talks like a friend", desc: "GenZ tone, real numbers — never a guess dressed up as fact." },
            { title: "Tracks investments", desc: "Live fund data, risk profiling, zero jargon." },
            { title: "Honest about uncertainty", desc: "Flags what it's not sure about instead of guessing silently." },
          ].map((f) => (
            <div
              key={f.title}
              className="group p-6 rounded-2xl border border-hairline bg-elevated/60
                         hover:border-gold hover:-translate-y-1 transition-all duration-300 ease-out"
            >
              <h3 className="font-display text-xl mb-2 text-forest">{f.title}</h3>
              <p className="text-sm text-ink-soft leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA footer */}
      <section className="relative glass-forest">
        <div className="max-w-3xl mx-auto px-6 sm:px-8 py-20 text-center">
          <h2 className="font-display text-3xl sm:text-4xl text-base italic mb-6">
            Money conversations, minus the shame.
          </h2>
          <MagneticButton>Try NeetiAi free →</MagneticButton>
        </div>
      </section>
    </main>
  );
}