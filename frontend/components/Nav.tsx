export default function Nav() {
  return (
    <nav className="sticky top-0 z-50 glass">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
        <span className="font-display text-xl italic text-forest">NeetiAi</span>
        <div className="hidden sm:flex items-center gap-8 text-sm font-medium text-ink-soft">
          <a href="#features" className="hover:text-forest transition-colors duration-200 ease-out">Features</a>
          <a href="#chat" className="hover:text-forest transition-colors duration-200 ease-out">Chat</a>
          <a href="#" className="hover:text-forest transition-colors duration-200 ease-out">Dashboard</a>
        </div>
        <button className="text-sm font-semibold px-5 py-2 rounded-full bg-forest text-base
                           hover:bg-ink transition-colors duration-200 ease-out">
          Get started
        </button>
      </div>
    </nav>
  );
}