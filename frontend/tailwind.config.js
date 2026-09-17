/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Zayado palette (matches the legacy a-main shop design)
        aubergine: { DEFAULT: "#1a3a6e", deep: "#0c1d33" },
        navy: { DEFAULT: "#1a3a6e", deep: "#0c1d33", dark: "#102945", nuance: "#1f4377" },
        gold: { DEFAULT: "#b89855", soft: "#d4b982", deep: "#9c7d40" },
        cream: { DEFAULT: "#f6f3ee", soft: "#f2efe7", dark: "#e8e2d4" },
        ink: { DEFAULT: "#1a1815", soft: "#4a4538", muted: "#6b6358" },
        sand: { DEFAULT: "#f3e9d0", 100: "#f2efe7", 200: "#f3e9d0", 300: "#e2dac7" },
        outline: "#e2dac7",
        canvasSoft: "#FBF6EA",
        // shadcn-style tokens still consumed by some components
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Poppins", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["Fraunces", "Georgia", "serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};
