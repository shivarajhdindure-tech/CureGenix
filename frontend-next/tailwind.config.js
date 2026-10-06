/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#04070e",
          900: "#080d18",
          800: "#0d1424",
          700: "#131c31",
          600: "#1b2640",
        },
        // kept for backwards compatibility with the previous theme
        bio: {
          bg: "#070b1a",
          card: "rgba(15,23,42,0.55)",
          cyan: "#22d3ee",
          purple: "#a78bfa",
          green: "#34d399",
        },
      },
      boxShadow: {
        neon: "0 0 30px rgba(34,211,238,0.22)",
        glow: "0 0 0 1px rgba(34,211,238,0.25), 0 8px 40px -12px rgba(34,211,238,0.35)",
      },
      keyframes: {
        floatSlow: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.85" },
        },
        spinSlow: { to: { transform: "rotate(360deg)" } },
        spinSlowReverse: { to: { transform: "rotate(-360deg)" } },
        sweep: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(350%)" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        barGrow: {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
      },
      animation: {
        floatSlow: "floatSlow 8s ease-in-out infinite",
        pulseGlow: "pulseGlow 3s ease-in-out infinite",
        spinSlow: "spinSlow 28s linear infinite",
        spinSlowReverse: "spinSlowReverse 40s linear infinite",
        sweep: "sweep 2.4s ease-in-out infinite",
        fadeUp: "fadeUp 0.5s ease-out both",
        barGrow: "barGrow 0.8s ease-out both",
      },
    },
  },
  plugins: [],
};
