/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        industrial: {
          50: "#f4f6f8",
          100: "#e4e9ee",
          200: "#c8d2dc",
          300: "#a1b1c1",
          400: "#7389a0",
          500: "#556e86",
          600: "#44576f",
          700: "#39485b",
          800: "#323e4d",
          900: "#1a2129",
          950: "#0f1319",
        },
        accent: {
          500: "#f5a623",
          600: "#dd8f10",
        },
      },
    },
  },
  plugins: [],
};
