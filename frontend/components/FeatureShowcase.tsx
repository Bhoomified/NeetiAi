const FEATURES = [
  { n: "01", title: "It sorts your spending", body: "Tell it what you bought — it figures out the category itself, learns from messy real transaction text.", tone: "olive" },
  { n: "02", title: "It sees next week coming", body: "Forecasts built on how you actually spend, not a generic template.", tone: "navy" },
  { n: "03", title: "It protects what matters", body: "When money's tight, it cuts discretionary spend first — never your rent or fees.", tone: "wine" },
  { n: "04", title: "It talks like a friend", body: "Ask Kuber anything about your money. No jargon, no judgment, always grounded in real numbers.", tone: "gold" },
  { n: "05", title: "It knows the market", body: "Live fund tracking and a risk quiz that actually makes sense — informational, never pushy.", tone: "olive" },
];

const TONE: Record<string, string> = {
  olive: "bg-olive/10 text-olive border-olive/30",
  navy: "bg-navy/10 text-navy border-navy/30",
  wine: "bg-wine/10 text-wine border-wine/30",
  gold: "bg-gold/10 text-forest border-gold/40",
};

export default function FeatureShowcase() {
  return (
    <div className="max-w-3xl mx-auto">
      <p className="text-center text-sm tracking-[0.2em] uppercase text-gold font-semibold mb-2">
        NeetiAi, plainly
      </p>
      <h2 className="font-display text-3xl sm:text-4xl text-center mb-12">
        Five things it actually does for you
      </h2>
      <div className="space-y-5">
        {FEATURES.map((f) => (
          <div
            key={f.n}
            className="flex items-start gap-5 p-5 rounded-3xl glass border border-hairline
                       hover:border-gold hover:-translate-y-0.5 transition-all duration-300 ease-out"
          >
            <span className={`shrink-0 w-11 h-11 rounded-full border flex items-center justify-center
                               font-display text-sm ${TONE[f.tone]}`}>
              {f.n}
            </span>
            <div>
              <h3 className="font-display text-xl mb-1">{f.title}</h3>
              <p className="text-sm text-ink-soft leading-relaxed">{f.body}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}