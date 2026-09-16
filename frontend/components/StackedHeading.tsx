type Props = {
  serif: string;        // big serif word
  mono: string;         // small tracked word beneath
  align?: "left" | "center";
  size?: "hero" | "section";
};

export default function StackedHeading({ serif, mono, align = "center", size = "section" }: Props) {
  const isHero = size === "hero";
  return (
    <div className={align === "center" ? "text-center" : "text-left"}>
      <h1
        className={`font-display italic text-forest leading-[0.9] ${
          isHero ? "text-7xl sm:text-9xl" : "text-4xl sm:text-5xl"
        }`}
      >
        {serif}
      </h1>
      <p
        className={`tabular uppercase text-ink-soft mt-2 ${
          isHero ? "text-[10px] sm:text-xs tracking-[0.5em]" : "text-[9px] sm:text-[10px] tracking-[0.35em]"
        }`}
      >
        {mono}
      </p>
    </div>
  );
}