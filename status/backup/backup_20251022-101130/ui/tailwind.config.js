/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{ts,tsx,js,jsx}",
    "./components/**/*.{ts,tsx,js,jsx}"
  ],
  theme: {
    extend: {
      boxShadow: {
        kirki: "0 4px 12px 0 rgba(0,0,0,0.06)"
      },
      borderRadius: {
        card: "1.5rem"
      }
    }
  },
  plugins: []
}
