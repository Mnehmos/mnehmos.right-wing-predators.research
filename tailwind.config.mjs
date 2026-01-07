/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Mnehmos brand - Stone palette with copper accent
        surface: {
          DEFAULT: '#292524', // Stone 800
          dark: '#1c1917',    // Stone 900
          light: '#44403c',   // Stone 700
        },
        muted: '#a8a29e',     // Stone 400
        accent: '#b87333',    // Copper
        danger: '#ef4444',    // Red 500
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: '#e7e5e4', // stone-200
            '--tw-prose-body': '#e7e5e4',
            '--tw-prose-headings': '#fafaf9',
            '--tw-prose-lead': '#a8a29e',
            '--tw-prose-links': '#b87333',
            '--tw-prose-bold': '#fafaf9',
            '--tw-prose-counters': '#a8a29e',
            '--tw-prose-bullets': '#78716c',
            '--tw-prose-hr': '#44403c',
            '--tw-prose-quotes': '#e7e5e4',
            '--tw-prose-quote-borders': '#b87333',
            '--tw-prose-captions': '#a8a29e',
            '--tw-prose-code': '#d4956a',
            '--tw-prose-pre-code': '#e7e5e4',
            '--tw-prose-pre-bg': '#292524',
            '--tw-prose-th-borders': '#57534e',
            '--tw-prose-td-borders': '#44403c',
            '--tw-prose-invert-body': '#e7e5e4',
            '--tw-prose-invert-headings': '#fafaf9',
            '--tw-prose-invert-lead': '#a8a29e',
            '--tw-prose-invert-links': '#b87333',
            '--tw-prose-invert-bold': '#fafaf9',
            '--tw-prose-invert-counters': '#a8a29e',
            '--tw-prose-invert-bullets': '#78716c',
            '--tw-prose-invert-hr': '#44403c',
            '--tw-prose-invert-quotes': '#e7e5e4',
            '--tw-prose-invert-quote-borders': '#b87333',
            '--tw-prose-invert-captions': '#a8a29e',
            '--tw-prose-invert-code': '#d4956a',
            '--tw-prose-invert-pre-code': '#e7e5e4',
            '--tw-prose-invert-pre-bg': '#292524',
            '--tw-prose-invert-th-borders': '#57534e',
            '--tw-prose-invert-td-borders': '#44403c',
          },
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        sans: ['Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
