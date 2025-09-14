import designTokens from './design-tokens.json';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: designTokens.colors.primary['50'].value,
          100: designTokens.colors.primary['100'].value,
          200: designTokens.colors.primary['200'].value,
          300: designTokens.colors.primary['300'].value,
          400: designTokens.colors.primary['400'].value,
          500: designTokens.colors.primary['500'].value,
          600: designTokens.colors.primary['600'].value,
          700: designTokens.colors.primary['700'].value,
          800: designTokens.colors.primary['800'].value,
          900: designTokens.colors.primary['900'].value,
        },
        gray: {
          50: designTokens.colors.gray['50'].value,
          100: designTokens.colors.gray['100'].value,
          200: designTokens.colors.gray['200'].value,
          300: designTokens.colors.gray['300'].value,
          400: designTokens.colors.gray['400'].value,
          500: designTokens.colors.gray['500'].value,
          600: designTokens.colors.gray['600'].value,
          700: designTokens.colors.gray['700'].value,
          800: designTokens.colors.gray['800'].value,
          900: designTokens.colors.gray['900'].value,
        },
        success: {
          50: designTokens.colors.success['50'].value,
          500: designTokens.colors.success['500'].value,
          600: designTokens.colors.success['600'].value,
          700: designTokens.colors.success['700'].value,
        },
        warning: {
          50: designTokens.colors.warning['50'].value,
          500: designTokens.colors.warning['500'].value,
          600: designTokens.colors.warning['600'].value,
          700: designTokens.colors.warning['700'].value,
        },
        error: {
          50: designTokens.colors.error['50'].value,
          500: designTokens.colors.error['500'].value,
          600: designTokens.colors.error['600'].value,
          700: designTokens.colors.error['700'].value,
        },
      },
      spacing: {
        xs: designTokens.spacing.xs.value,
        sm: designTokens.spacing.sm.value,
        md: designTokens.spacing.md.value,
        lg: designTokens.spacing.lg.value,
        xl: designTokens.spacing.xl.value,
        '2xl': designTokens.spacing['2xl'].value,
        '3xl': designTokens.spacing['3xl'].value,
      },
      fontFamily: {
        sans: designTokens.typography.fontFamily.sans.value.split(', '),
        mono: designTokens.typography.fontFamily.mono.value.split(', '),
      },
      fontSize: {
        xs: designTokens.typography.fontSize.xs.value,
        sm: designTokens.typography.fontSize.sm.value,
        base: designTokens.typography.fontSize.base.value,
        lg: designTokens.typography.fontSize.lg.value,
        xl: designTokens.typography.fontSize.xl.value,
        '2xl': designTokens.typography.fontSize['2xl'].value,
        '3xl': designTokens.typography.fontSize['3xl'].value,
        '4xl': designTokens.typography.fontSize['4xl'].value,
      },
      fontWeight: {
        normal: designTokens.typography.fontWeight.normal.value,
        medium: designTokens.typography.fontWeight.medium.value,
        semibold: designTokens.typography.fontWeight.semibold.value,
        bold: designTokens.typography.fontWeight.bold.value,
      },
      lineHeight: {
        tight: designTokens.typography.lineHeight.tight.value,
        normal: designTokens.typography.lineHeight.normal.value,
        relaxed: designTokens.typography.lineHeight.relaxed.value,
      },
      borderRadius: {
        none: designTokens.borderRadius.none.value,
        sm: designTokens.borderRadius.sm.value,
        md: designTokens.borderRadius.md.value,
        lg: designTokens.borderRadius.lg.value,
        xl: designTokens.borderRadius.xl.value,
        full: designTokens.borderRadius.full.value,
      },
      boxShadow: {
        sm: designTokens.shadow.sm.value,
        md: designTokens.shadow.md.value,
        lg: designTokens.shadow.lg.value,
        xl: designTokens.shadow.xl.value,
      },
      screens: {
        sm: designTokens.breakpoints.sm.value,
        md: designTokens.breakpoints.md.value,
        lg: designTokens.breakpoints.lg.value,
        xl: designTokens.breakpoints.xl.value,
        '2xl': designTokens.breakpoints['2xl'].value,
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
