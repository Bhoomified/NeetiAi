type Props = {
  children: React.ReactNode;
  speed?: number;          // seconds per loop
  reverse?: boolean;
  className?: string;
};

// Seamless horizontal ticker — content is rendered twice and the track slides
// by exactly one copy, so the loop never shows a seam. Pauses on hover.
export default function Marquee({ children, speed = 40, reverse = false, className = "" }: Props) {
  return (
    <div className={`marquee group relative overflow-hidden ${className}`}>
      <div
        className="marquee-track flex w-max group-hover:[animation-play-state:paused]"
        style={{ animationDuration: `${speed}s`, animationDirection: reverse ? "reverse" : "normal" }}
      >
        <div className="flex shrink-0 items-center">{children}</div>
        <div className="flex shrink-0 items-center" aria-hidden>{children}</div>
      </div>
    </div>
  );
}
