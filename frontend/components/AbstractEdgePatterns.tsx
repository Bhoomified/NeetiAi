export default function AbstractEdgePatterns() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden -z-10" aria-hidden="true">
      {/* Top-left organic wash */}
      <svg className="absolute -top-16 -left-24 w-[26rem] h-[26rem] opacity-[0.55]" viewBox="0 0 400 400" fill="none">
        <path d="M50 0 C 150 20, 100 120, 200 140 S 380 100, 400 200 L 400 0 Z" fill="#183630" opacity="0.08" />
        <path d="M0 60 C 100 40, 80 160, 180 180 S 320 140, 340 260" stroke="#C9A15E" strokeWidth="1.5" fill="none" opacity="0.5" />
      </svg>

      {/* Bottom-right organic wash */}
      <svg className="absolute -bottom-20 -right-20 w-[28rem] h-[28rem] opacity-[0.55]" viewBox="0 0 400 400" fill="none">
        <path d="M400 400 C 300 380, 340 280, 240 260 S 60 300, 40 200 L 0 400 Z" fill="#6B2E2A" opacity="0.06" />
        <path d="M400 340 C 300 360, 320 240, 220 220 S 80 260, 60 140" stroke="#C9A15E" strokeWidth="1.5" fill="none" opacity="0.5" />
      </svg>

      {/* Right-mid sage wash */}
      <svg className="absolute top-[45%] -right-16 w-72 h-72 opacity-[0.4]" viewBox="0 0 300 300" fill="none">
        <path d="M300 0 C 220 40, 260 140, 180 160 S 40 130, 0 220 L 0 0 Z" fill="#8A9A83" opacity="0.1" />
      </svg>
    </div>
  );
}