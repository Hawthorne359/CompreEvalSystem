/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Noto Sans SC"', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#fdf2f5',
          100: '#fbe8ee',
          500: '#c8102e',
          600: '#a90d27',
          700: '#8f0b21',
        },
      },
      boxShadow: {
        soft: '0 12px 32px rgba(60,15,30,0.08), 0 4px 12px rgba(0,0,0,0.04)',
      },
      borderRadius: {
        app: '16px',
      },
    },
  },
  plugins: [],
}
