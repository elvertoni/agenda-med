/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        // Design system tokens — see PRD §9
        surface: {
          base: '#020617',     // slate-950 — page background
          raised: '#0f172a',   // slate-900 — cards, panels
          border: '#1e293b',   // slate-800 — subtle borders
        },
        ink: {
          primary: '#f1f5f9',  // slate-100 — primary text
          muted: '#94a3b8',    // slate-400 — secondary text
        },
        accent: {
          DEFAULT: '#10b981',  // emerald-500 — primary actions
          soft: '#34d399',     // emerald-400 — hover/highlight
          link: '#38bdf8',     // sky-400 — links, secondary accent
        },
        danger: '#fb7185',     // rose-400 — errors
      },
      backgroundImage: {
        'brand-gradient':
          'linear-gradient(to bottom right, #10b981, #14b8a6, #0284c7)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
