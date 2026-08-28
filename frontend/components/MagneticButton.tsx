"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function MagneticButton({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLButtonElement>(null);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const { session } = useAuth();
  const router = useRouter();

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    setPos({
      x: (e.clientX - rect.left - rect.width / 2) * 0.3,
      y: (e.clientY - rect.top - rect.height / 2) * 0.3,
    });
  };

  return (
    <button
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setPos({ x: 0, y: 0 })}
      onClick={() => router.push(session ? "/dashboard" : "/login")}
      style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}
      className="group relative px-8 py-4 bg-forest text-white rounded-full font-medium
                 transition-transform duration-200 ease-out hover:shadow-lg hover:shadow-forest/20"
    >
      <span className="relative z-10">{children}</span>
    </button>
  );
}