import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#eef7ff",
        muted: "#91a4c5",
        cyan: "#38d9ff",
        glassblue: "#60a5fa",
        green: "#3ff6a8",
        violet: "#9d7cff",
      },
    },
  },
  plugins: [],
};

export default config;
