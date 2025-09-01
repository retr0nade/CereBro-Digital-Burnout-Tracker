// Design Token Layer
// Modern, commercial-grade design system tokens

// Color tokens - Dark theme with high contrast
export const colors = {
  // Backgrounds
  bg: '#0a0a0a',
  surface: '#131313',
  surfaceAlt: '#1a1a1a',
  
  // Text
  text: '#f4f4f5',
  textMuted: '#a1a1aa',
  
  // Brand
  brand: '#3b82f6',
  brandHover: '#2563eb',
  brandActive: '#1d4ed8',
  
  // Status colors
  ok: '#10b981',
  okMuted: '#064e3b',
  warn: '#f59e0b',
  warnMuted: '#78350f',
  danger: '#ef4444',
  dangerMuted: '#7f1d1d',
  
  // Interactive
  border: '#27272a',
  borderHover: '#3f3f46',
  focus: '#3b82f6',
  
  // Overlays
  overlay: 'rgba(0, 0, 0, 0.8)',
  backdrop: 'rgba(0, 0, 0, 0.25)',
} as const;

// Radii
export const radii = {
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1.25rem',
  '2xl': '1.5rem',
  full: '9999px',
} as const;

// Shadow presets
export const shadows = {
  soft: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  lift: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  pop: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  glow: '0 0 0 1px rgba(59, 130, 246, 0.1), 0 0 20px rgba(59, 130, 246, 0.1)',
} as const;

// Blur levels
export const blur = {
  none: '0',
  sm: '4px',
  md: '8px',
  lg: '16px',
  xl: '24px',
} as const;

// Spacing scale helpers
export const spacing = {
  gapSm: '0.5rem',   // 8px
  gap: '1rem',       // 16px
  gapLg: '1.5rem',   // 24px
  gapXl: '2rem',     // 32px
  section: '3rem',   // 48px
  page: '4rem',      // 64px
} as const;

// Typography scale
export const typography = {
  fontFamily: {
    sans: ['Inter', 'Spline Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
  },
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '0.969rem',   // 15.5px (increased base)
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
  },
  lineHeight: {
    tight: '1.25',
    normal: '1.6',      // Increased base line height
    relaxed: '1.75',
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
} as const;

// Transition presets
export const transitions = {
  fast: '150ms ease-out',
  normal: '200ms ease-out',
  slow: '300ms ease-out',
  bounce: '300ms cubic-bezier(0.68, -0.55, 0.265, 1.55)',
} as const;

// Z-index scale
export const zIndex = {
  hide: -1,
  base: 0,
  raised: 10,
  dropdown: 100,
  sticky: 200,
  overlay: 300,
  modal: 400,
  tooltip: 500,
  toast: 600,
} as const;

// Export all tokens as a single object for easy consumption
export const tokens = {
  colors,
  radii,
  shadows,
  blur,
  spacing,
  typography,
  transitions,
  zIndex,
} as const;

export default tokens;
