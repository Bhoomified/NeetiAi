export default function Nav() {
  return (
    <nav className="sticky top-0 z-50 glass">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
        <a href="/" className="font-display text-xl italic text-forest">NeetiAi</a>
        <div className="hidden sm:flex items-center gap-8 text-sm font-medium text-ink-soft">
          <a href="/#features" className="hover:text-forest transition-colors duration-200 ease-out">Features</a>
          <a href="/dashboard" className="hover:text-forest transition-colors duration-200 ease-out">Dashboard</a>
          <a href="/budget" className="hover:text-forest transition-colors duration-200 ease-out">Budget</a>
          <a href="/chat" className="hover:text-forest transition-colors duration-200 ease-out">Chat</a>
        </div>
        <a
          href="/dashboard"
          className="text-sm font-semibold px-5 py-2 rounded-full bg-forest
                     hover:bg-ink transition-colors duration-200 ease-out"
        >
          Get started
        </a>
      </div>
    </nav>
  );
}