/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
      },
      colors: {
        sidebar: "#1A1A2E",
        "nav-active": "#2E75B6",
        primary: "#1565C0",
        accent: "#E65100",
        success: "#2E7D32",
        danger: "#C62828",
        warning: "#F57F17",
        surface: "#FFFFFF",
        base: "#F5F7FA",
      },
    },
  },
  plugins: [],
};
