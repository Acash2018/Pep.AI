import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        pitch: '#0F172A',
        accent: '#10B981',
        panel: '#111827',
        muted: '#6B7280',
      },
    },
  },
  plugins: [],
};

export default config;
