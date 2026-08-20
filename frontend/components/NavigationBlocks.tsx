const BLOCKS = [
  { title: "Dashboard", href: "/dashboard", hover: "See where your money actually went →" },
  { title: "Budget", href: "/budget", hover: "Build a savings plan that fits you →" },
  { title: "Chat", href: "/chat", hover: "Ask Kuber anything, money or otherwise →" },
  { title: "Investments", href: "/investments", hover: "Know your risk, track your funds →" },
];

export default function NavigationBlocks() {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 max-w-5xl mx-auto">
      {BLOCKS.map((b) => (
        <a
          key={b.title}
          href={b.href}
          className="group relative h-40 rounded-3xl glass border border-hairline overflow-hidden
                     hover:border-gold hover:-translate-y-1 transition-all duration-300 ease-out flex items-end p-5"
        >
          <span className="font-display text-2xl text-forest group-hover:opacity-0 transition-opacity duration-200 ease-out">
            {b.title}
          </span>
          <span className="absolute inset-0 flex items-center justify-center text-center px-6 text-sm font-medium text-ink
                            opacity-0 group-hover:opacity-100 bg-paper/95 transition-opacity duration-200 ease-out">
            {b.hover}
          </span>
        </a>
      ))}
    </div>
  );
}