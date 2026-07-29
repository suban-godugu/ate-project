/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f4f7fb",
          100: "#e6edf6",
          200: "#c9d7ea",
          300: "#9fb6d3",
          400: "#6f8fb8",
          500: "#4d6f9a",
          600: "#3a567c",
          700: "#2f4564",
          800: "#293a53",
          900: "#243246",
          950: "#141c28",
        },
        signal: {
          good: "#1f9d63",
          fail: "#d64545",
          warn: "#c9851a",
          info: "#2f6fed",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Segoe UI", "sans-serif"],
        display: ["var(--font-display)", "Segoe UI", "sans-serif"],
        mono: ["var(--font-mono)", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 10px 30px rgba(20, 28, 40, 0.08)",
      },
    },
  },
  plugins: [],
};
