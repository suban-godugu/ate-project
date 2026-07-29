import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#090B12",
        card: "#111827",
        border: "#2D3748",
        primary: "#7C3AED",
        danger: "#EF4444",
        success: "#10B981",
        warning: "#F59E0B",
        muted: "#94A3B8",
      },
      fontFamily: {
        display: ["var(--font-display)", "Segoe UI", "sans-serif"],
        body: ["var(--font-body)", "Segoe UI", "sans-serif"],
      },
      borderRadius: {
        glass: "20px",
      },
    },
  },
  plugins: [],
} satisfies Config;
