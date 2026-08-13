import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: { 950: "#05070b", 900: "#090d14", 850: "#0d131c", 800: "#111a26" },
        mineral: { lithium: "#a78bfa", copper: "#f59e0b", cobalt: "#60a5fa", nickel: "#34d399", rare: "#f472b6" }
      },
      boxShadow: { glass: "0 18px 60px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.06)" }
    }
  },
  plugins: []
} satisfies Config;
