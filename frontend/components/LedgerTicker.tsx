import Marquee from "./Marquee";

const MAXIMS = [
  "Compound interest, quietly",
  "Est. MMXXVI",
  "Spend with intent",
  "A rupee saved is a rupee earned",
  "Patience pays dividends",
  "Know where every rupee goes",
  "Prudence over impulse",
  "Wealth is what you don't spend",
];

const FIGURES = [
  { label: "NIFTY 50", value: "Index · long horizon" },
  { label: "SIP", value: "from ₹500 / month" },
  { label: "SAVINGS RATE", value: "aim for 20%" },
  { label: "EMERGENCY FUND", value: "3–6 months" },
  { label: "RULE", value: "50 · 30 · 20" },
  { label: "INFLATION", value: "the silent tax" },
];

// Two-band "ledger tape": serif maxims on forest, mono figures on paper,
// sliding in opposite directions.
export default function LedgerTicker() {
  return (
    <div className="relative border-y border-gold/40 select-none">
      <div className="bg-forest py-3">
        <Marquee speed={55}>
          {MAXIMS.map((m) => (
            <span key={m} className="flex items-center">
              <span className="font-display italic text-xl sm:text-2xl text-paper px-6 whitespace-nowrap">{m}</span>
              <span className="text-gold text-sm">✦</span>
            </span>
          ))}
        </Marquee>
      </div>
      <div className="bg-paper py-2 border-t border-gold/40">
        <Marquee speed={45} reverse>
          {FIGURES.map((f) => (
            <span key={f.label} className="tabular text-[11px] tracking-[0.2em] uppercase whitespace-nowrap px-6">
              <span className="text-gold">{f.label}</span>
              <span className="text-ink-soft"> — {f.value}</span>
              <span className="text-hairline pl-6">|</span>
            </span>
          ))}
        </Marquee>
      </div>
    </div>
  );
}
