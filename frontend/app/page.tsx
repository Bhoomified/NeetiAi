import Nav from "@/components/Nav";
import FinanceLineArt from "@/components/FinanceLineArt";
import AbstractEdgePatterns from "@/components/AbstractEdgePatterns";
import StickyTagline from "@/components/StickyTagline";
import FeatureShowcase from "@/components/FeatureShowcase";
import NavigationBlocks from "@/components/NavigationBlocks";
import FloatingAssistant from "@/components/FloatingAssistant";
import MagneticButton from "@/components/MagneticButton";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-x-hidden">
      <AbstractEdgePatterns />
      <FinanceLineArt />
      <Nav />
      <StickyTagline />
      <FloatingAssistant />

      <section className="relative max-w-2xl mx-auto px-6 sm:px-8 pt-8 pb-16 text-center">
        <p className="text-lg text-ink-soft leading-relaxed mb-10">
          Your money, actually explained — not tracked in a spreadsheet you'll forget to open.
        </p>
        <MagneticButton>Start tracking →</MagneticButton>
      </section>

      <section className="relative px-6 sm:px-8 pb-24">
        <NavigationBlocks />
      </section>

      <section id="features" className="relative px-6 sm:px-8 pb-32">
        <FeatureShowcase />
      </section>

      <section className="relative glass-forest">
        <div className="max-w-3xl mx-auto px-6 sm:px-8 py-20 text-center">
          <h2 className="font-display text-3xl sm:text-4xl text-paper italic mb-6">
            Money conversations, minus the shame.
          </h2>
          <MagneticButton>Try NeetiAi free →</MagneticButton>
        </div>
      </section>
    </main>
  );
}
