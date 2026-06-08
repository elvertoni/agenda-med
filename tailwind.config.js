/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50:  '#f0f5ff',
          100: '#e0ebff',
          200: '#c3d5fe',
          300: '#96b4fc',
          400: '#6089f8',
          500: '#3a61f2',
          600: '#2445e7',
          700: '#1c34cc',
          800: '#1c2da5',
          900: '#1c2b82',  // main brand navy
          950: '#11194d',  // darkest nav
        },
        health: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',  // primary CTA
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
          950: '#042f2e',
        },
      },
      fontFamily: {
        display: ['"DM Serif Display"', 'Georgia', 'Cambria', '"Times New Roman"', 'serif'],
        sans:    ['"DM Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'navy-sm': '0 1px 2px 0 rgb(28 43 130 / 0.15)',
        'navy':    '0 4px 6px -1px rgb(28 43 130 / 0.2), 0 2px 4px -2px rgb(28 43 130 / 0.1)',
        'navy-lg': '0 10px 15px -3px rgb(28 43 130 / 0.25), 0 4px 6px -4px rgb(28 43 130 / 0.1)',
      },
      backgroundImage: {
        'brand-gradient':
          'linear-gradient(135deg, #1c2b82 0%, #1d4ed8 40%, #0d9488 100%)',
        'brand-gradient-light':
          'linear-gradient(135deg, #1c2b82 0%, #2563eb 50%, #0f766e 100%)',
      },
    },
  },
  plugins: [],
};
