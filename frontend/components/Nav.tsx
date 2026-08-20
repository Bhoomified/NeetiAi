export default function Nav() {
  return (
    <nav className="sticky top-0 z-50 glass">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
        <a href="/" className="font-display text-xl italic text-forest">NeetiAi</a>
        <div className="hidden sm:flex items-center gap-6 text-sm font-medium text-ink-soft overflow-x-auto">
          <a href="/dashboard" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Dashboard</a>
          <a href="/budget" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Budget</a>
          <a href="/chat" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Chat</a>
          <a href="/investments" className="hover:text-forest transition-colors duration-200 ease-out whitespace-nowrap">Investments</a>
        </div>

        <a
          href="/dashboard"
          className="text-sm font-semibold px-5 py-2 rounded-full bg-forest text-white
                     hover:bg-ink transition-colors duration-200 ease-out whitespace-nowrap"
        >
          Get started
        </a>
      </div>
    </nav>
  );
}