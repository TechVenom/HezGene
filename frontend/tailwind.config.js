/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#f4f5f9',
          secondary: '#ffffff',
          tertiary: '#f8f9fa',
        },
        accent: {
          green: '#10b981',
          cyan: '#0ea5e9',
          purple: '#673ab7',
          red: '#ef4444',
          yellow: '#f59e0b',
          pink: '#ec4899',
        },
        text: {
          primary: '#111827',
          secondary: '#6b7280',
        },
        border: '#e5e7eb',
      }
    },
  },
  plugins: [],
}
