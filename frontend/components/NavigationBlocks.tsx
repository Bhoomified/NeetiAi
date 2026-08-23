const BLOCKS = [
  { title: "Dashboard", href: "/dashboard", hover: "See where your money went", tone: "navy" },
  { title: "Budget", href: "/budget", hover: "Build a plan that fits you", tone: "olive" },
  { title: "Chat", href: "/chat", hover: "Ask Kuber, anytime", tone: "wine" },
  { title: "Investments", href: "/investments", hover: "Know your risk, track your funds", tone: "gold" },
];

const TONE: Record<string, string> = {
  navy: "bg-navy/[0.06] border-navy/50 hover:border-navy/60",
  olive: "bg-olive/[0.06] border-olive/50 hover:border-olive/60",
  wine: "bg-wine/[0.06] border-wine/50 hover:border-wine/60",
  gold: "bg-gold/[0.09] border-gold/50 hover:border-gold/70",
};

export default function NavigationBlocks() {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 max-w-5xl mx-auto">
      {BLOCKS.map((b) => (
        <a
          key={b.title}
          href={b.href}
          className={`group h-40 rounded-3xl border flex flex-col items-center justify-center text-center px-5
                      hover:-translate-y-1 transition-all duration-300 ease-out ${TONE[b.tone]}`}
        >
          <span className="font-display text-3xl text-forest mb-2">{b.title}</span>
          <span className="text-lg text-ink-soft opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-out">
            {b.hover}
          </span>
        </a>
      ))}
    </div>
  );
}