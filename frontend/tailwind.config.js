export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        scaler: {
          primary: '#1F2937',
          accent: '#3B82F6',
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          background: '#F9FAFB',
          'text-dark': '#1F2937',
          'text-light': '#6B7280',
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
