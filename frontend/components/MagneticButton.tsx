"use client";

import { useRef, useState } from "react";

export default function MagneticButton({
  children, onClick,
}: { children: React.ReactNode; onClick?: () => void }) {
  const ref = useRef<HTMLButtonElement>(null);
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) * 0.3;
    const y = (e.clientY - rect.top - rect.height / 2) * 0.3;
    setPos({ x, y });
  };

  return (
    <button
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setPos({ x: 0, y: 0 })}
      onClick={onClick}
      style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}
      className="group relative px-8 py-4 bg-forest text-base rounded-full font-medium
                 transition-transform duration-200 ease-out hover:shadow-lg hover:shadow-forest/20"
    >
      <span className="relative z-10">{children}</span>
    </button>
  );
}