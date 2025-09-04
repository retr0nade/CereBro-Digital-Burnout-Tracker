module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1440px',
      },
    },
    extend: {
      colors: {
        // CSS variable-based colors for theming
        bg: 'var(--color-bg)',
        surface: 'var(--color-surface)',
        'surface-alt': 'var(--color-surface-alt)',
        text: 'var(--color-text)',
        'text-muted': 'var(--color-text-muted)',
        brand: {
          DEFAULT: 'var(--color-brand)',
          hover: 'var(--color-brand-hover)',
          active: 'var(--color-brand-active)',
        },
        ok: {
          DEFAULT: 'var(--color-ok)',
          muted: 'var(--color-ok-muted)',
        },
        warn: {
          DEFAULT: 'var(--color-warn)',
          muted: 'var(--color-warn-muted)',
        },
        danger: {
          DEFAULT: 'var(--color-danger)',
          muted: 'var(--color-danger-muted)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          hover: 'var(--color-border-hover)',
        },
        focus: 'var(--color-focus)',
        overlay: 'var(--color-overlay)',
        backdrop: 'var(--color-backdrop)',
      },
      borderRadius: {
        '2xl': '1.5rem',
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
        lift: 'var(--shadow-lift)',
        pop: 'var(--shadow-pop)',
        glow: 'var(--shadow-glow)',
        card: 'var(--shadow-card)',
        'card-hover': 'var(--shadow-card-hover)',
      },
      backdropBlur: {
        xs: '2px',
      },
      fontFamily: {
        sans: ['Inter', 'Spline Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      fontSize: {
        base: '0.969rem', // 15.5px
      },
      lineHeight: {
        normal: '1.6',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    function({ addBase, theme }) {
      addBase({
        // Set default border radius
        '*': {
          borderRadius: theme('borderRadius.2xl'),
        },
        // Override for specific elements that shouldn't have rounded corners
        'input[type="range"], progress, hr': {
          borderRadius: '0',
        },
      });
    },
  ],
};
