/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f18",
        slate: "#1a2433",
        fog: "#e9eef6",
        accent: "#f97316",
        accentSoft: "#ffd6b0",
        sea: "#1b4965",
        mint: "#62b6cb"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(249,115,22,0.15), 0 8px 30px rgba(15,23,42,0.25)"
      }
    }
  },
  plugins: []
};
