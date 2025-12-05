import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
    './src/app/**/*.{ts,tsx}',
    './src/modules/**/*.{ts,tsx}',
    './src/lib/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        /* ============================================
         * SEMANTIC COLOR SYSTEM
         * All colors use CSS variables for theme support
         * See globals.css for variable definitions
         * ============================================ */

        // === SHADCN/UI COMPATIBILITY ===
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },

        // === SURFACE TOKENS (Background Layers) ===
        // Use these for layout backgrounds
        shell: "hsl(var(--surface-shell))",
        "card-bg": "hsl(var(--surface-primary))",
        elevated: "hsl(var(--surface-elevated))",
        // Semantic aliases for surfaces
        surface: {
          shell: "hsl(var(--surface-shell))",
          primary: "hsl(var(--surface-primary))",
          elevated: "hsl(var(--surface-elevated))",
        },

        // === TEXT TOKENS ===
        // Use these for typography hierarchy
        "text-strong": "hsl(var(--text-primary))",
        "text-body": "hsl(var(--text-secondary))",
        "text-muted": "hsl(var(--text-tertiary))",
        "text-subtle": "hsl(var(--text-quaternary))",
        // Semantic aliases for text
        text: {
          strong: "hsl(var(--text-primary))",
          body: "hsl(var(--text-secondary))",
          muted: "hsl(var(--text-tertiary))",
          subtle: "hsl(var(--text-quaternary))",
        },

        // === ACCENT TOKENS (Brand/Primary Action) ===
        accent: {
          DEFAULT: "hsl(var(--accent-primary))",
          hover: "hsl(var(--accent-primary-hover))",
          active: "hsl(var(--accent-primary-active))",
          foreground: "hsl(var(--accent-foreground))",
        },

        // === STATUS TOKENS (Semantic Colors) ===
        success: {
          DEFAULT: "hsl(var(--status-success))",
          emphasis: "hsl(var(--status-success-emphasis))",
          muted: "hsl(var(--status-success-muted))",
        },
        warning: {
          DEFAULT: "hsl(var(--status-warning))",
          emphasis: "hsl(var(--status-warning-emphasis))",
          muted: "hsl(var(--status-warning-muted))",
        },
        danger: {
          DEFAULT: "hsl(var(--status-danger))",
          emphasis: "hsl(var(--status-danger-emphasis))",
          muted: "hsl(var(--status-danger-muted))",
        },
        info: {
          DEFAULT: "hsl(var(--status-info))",
          emphasis: "hsl(var(--status-info-emphasis))",
          muted: "hsl(var(--status-info-muted))",
        },

        // === BORDER TOKENS ===
        "border-default": "hsl(var(--border-primary))",
        "border-muted": "hsl(var(--border-secondary))",
        "border-accent": "hsl(var(--accent-primary))",
        "border-danger": "hsl(var(--status-danger) / 0.5)",

        // === CHART TOKENS ===
        chart: {
          grid: "hsl(var(--chart-grid))",
          axis: "hsl(var(--chart-axis))",
          "series-1": "hsl(var(--chart-series-1))",
          "series-2": "hsl(var(--chart-series-2))",
          "series-3": "hsl(var(--chart-series-3))",
          "series-4": "hsl(var(--chart-series-4))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config