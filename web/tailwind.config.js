/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          light: '#ffffff',
          dark: '#111827',
        },
        border: {
          light: '#e5e7eb',
          dark: '#1f2937',
        },
      },
    },
  },
  plugins: [],
}
