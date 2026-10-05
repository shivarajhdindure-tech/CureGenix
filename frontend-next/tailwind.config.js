/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bio: {
          bg: "#070b1a",
          card: "rgba(15,23,42,0.55)",
          cyan: "#22d3ee",
          purple: "#a78bfa",
          green: "#34d399"
        }
      },
      boxShadow: {
        neon: "0 0 30px rgba(34,211,238,0.22)"
      },
      keyframes: {
        floatSlow: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" }
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.85" }
        }
      },
      animation: {
        floatSlow: "floatSlow 8s ease-in-out infinite",
        pulseGlow: "pulseGlow 3s ease-in-out infinite"
      }
    }
  },
  plugins: []
};
