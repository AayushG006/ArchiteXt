/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        slateInk: '#0b1324',
        cyanGlow: '#00d4ff',
        ember: '#ff6a3d'
      }
    }
  },
  plugins: []
}
