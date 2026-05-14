/** @type {import("tailwindcss").Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        unab: {
          blue: "#1F3864",
          light: "#2E75B6",
        }
      }
    },
  },
  plugins: [],
}