module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Avenir', 'Helvetica', 'Arial', 'sans-serif'],
      },
      colors: {
        primary: {
          DEFAULT: '#2563eb', // blue-600
          light: '#60a5fa', // blue-400
          dark: '#1e40af', // blue-800
        },
        accent: {
          DEFAULT: '#22c55e', // green-500
          light: '#bbf7d0', // green-100
        },
        warning: '#facc15', // yellow-400
        info: '#38bdf8', // sky-400
        success: '#4ade80', // green-400
        error: '#f87171', // red-400
      },
      boxShadow: {
        'soft': '0 4px 24px 0 rgba(34,197,94,0.08)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: 0, transform: 'translateY(-10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.5s ease-out',
      },
    },
  },
  plugins: [],
}; 