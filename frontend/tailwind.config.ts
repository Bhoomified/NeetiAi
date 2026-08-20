import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F5F0E6",
        elevated: "#FFFFFF",
        ink: { DEFAULT: "#1A2E1F", soft: "#4A5A47" },
        gold: "#C9A15E",
        forest: "#183630",
        rust: "#6B2E2A",
        sage: "#8A9A83",
        navy: "#1B2A44",
        wine: "#5C1F2E",
        olive: "#4A5320",
        hairline: "#D4CBB8",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        sans: ["var(--font-inter)", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;