/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bidpilot: {
          ink: "#172033",
          line: "#d8dee9",
          surface: "#f7f9fc",
          accent: "#0f766e",
        },
      },
    },
  },
  plugins: [],
};
