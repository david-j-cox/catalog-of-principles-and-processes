/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'terminal': ['Courier New', 'Courier', 'monospace'],
        'pixel': ['Press Start 2P', 'cursive'],
      },
      colors: {
        'terminal-green': '#00ff00',
        'terminal-amber': '#ffb000',
        'terminal-black': '#000000',
        'terminal-dark': '#0a0a0a',
        'terminal-gray': '#1a1a1a',
        'terminal-light-green': '#00cc00',
        'terminal-light-amber': '#ffcc00',
      },
      animation: {
        'blink': 'blink 1s infinite',
        'scan': 'scan 2s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        blink: {
          '0%, 50%': { opacity: '1' },
          '51%, 100%': { opacity: '0' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glow: {
          '0%': { textShadow: '0 0 5px #00ff00' },
          '100%': { textShadow: '0 0 20px #00ff00, 0 0 30px #00ff00' },
        },
      },
    },
  },
  plugins: [],
} 