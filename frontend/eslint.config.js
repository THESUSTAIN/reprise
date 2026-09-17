// Flat config (ESLint 9). Charge react-hooks + react uniquement pour que les
// directives `eslint-disable react-hooks/*` et `react/*` présentes dans le code
// soient reconnues. Aucune règle n'est activée : le lint ne bloque pas le build
// de cette app Vite importée.
import reactHooks from "eslint-plugin-react-hooks";
import react from "eslint-plugin-react";

export default [
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "build/**",
      "public/**",
      "src/pages/legacy/**",
      "**/*.min.js",
    ],
  },
  {
    files: ["**/*.{js,jsx}"],
    plugins: { "react-hooks": reactHooks, react },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    linterOptions: { reportUnusedDisableDirectives: "off" },
    rules: {},
  },
];
