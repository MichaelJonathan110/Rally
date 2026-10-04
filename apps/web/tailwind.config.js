/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: '1rem', sm: '1.5rem', lg: '2rem', '2xl': '3rem' },
      screens: { '2xl': '1536px' },
    },
    screens: {
      xs: '360px',
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
      '3xl': '1920px',
    },
    extend: {
      colors: {
        /* Paper base - warm off-white / beige (LIGHT system). */
        paper: { DEFAULT: '#FAF6F0', warm: '#F2ECE2' },
        surface: { DEFAULT: '#FFFFFF', muted: '#FBF8F3' },
        line: { DEFAULT: '#E8E0D4', strong: '#D9CFBE' },
        /* Ink - big bold near-black type + secondary greys. */
        ink: { DEFAULT: '#141414', 2: '#5C5C5C', 3: '#8A8A8A', inv: '#FFFFFF' },
        /* Pastel identity + data-viz colours. */
        cyan: { DEFAULT: '#9FE3DC', soft: '#DCF4F1' },
        mint: { DEFAULT: '#B9E9C9', soft: '#E3F6EA' },
        lime: { DEFAULT: '#D9F08C', soft: '#EFF9D6' },
        yellow: { DEFAULT: '#FFE28A', soft: '#FFF5D6' },
        coral: { DEFAULT: '#FF9C86', soft: '#FFE3DB' },
        violet: '#A87BE0',
        emerald: { DEFAULT: '#63C98A', soft: '#E3F6EA' },
        /* Semantic. `action` = the single deep-coral "do this" colour. */
        action: { DEFAULT: '#FF6F55', dark: '#F0523A', ink: '#FFFFFF' },
        success: '#4FBF8B',
        warning: '#F2C14E',
        danger: '#F07C6C',
      },
      fontFamily: {
        display: ['Sora', 'Archivo', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem', letterSpacing: '0.02em' }],
        display: ['clamp(2.75rem, 7vw, 5.5rem)', { lineHeight: '0.94', letterSpacing: '-0.035em' }],
        'display-sm': ['clamp(2rem, 4.5vw, 3.25rem)', { lineHeight: '1.0', letterSpacing: '-0.025em' }],
      },
      borderRadius: { sm: '0.625rem', md: '0.875rem', lg: '1.25rem', xl: '1.75rem', '2xl': '2.25rem' },
      boxShadow: {
        soft: '0 1px 2px rgba(20,20,20,0.04), 0 10px 30px -18px rgba(20,20,20,0.18)',
        lift: '0 24px 60px -28px rgba(20,20,20,0.28)',
        pop: '0 12px 40px -16px rgba(255,111,85,0.35)',
        ring: '0 0 0 1px rgba(20,20,20,0.06)',
      },
      spacing: { 'safe-b': 'env(safe-area-inset-bottom)', 'safe-t': 'env(safe-area-inset-top)' },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.16, 1, 0.3, 1)',
        snap: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      keyframes: {
        'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
        'slide-up': { from: { transform: 'translateY(14px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
        shimmer: { '100%': { transform: 'translateX(100%)' } },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-8px)' } },
        'pulse-ring': { '0%': { transform: 'scale(0.9)', opacity: '0.6' }, '100%': { transform: 'scale(1.6)', opacity: '0' } },
      },
      animation: {
        'fade-in': 'fade-in 220ms ease-out',
        'slide-up': 'slide-up 380ms cubic-bezier(0.16,1,0.3,1)',
        float: 'float 5s ease-in-out infinite',
        'pulse-ring': 'pulse-ring 1.8s cubic-bezier(0.16,1,0.3,1) infinite',
      },
    },
  },
  plugins: [],
};
