// Config ESLint racine (ESLint 9) — le linter de la plateforme s'exécute depuis /app.
// On ne lint QUE le frontend (JS/JSX), on ignore le backend Python et les .js
// hérités hors frontend. Plugins react/react-hooks chargés pour reconnaître les
// directives `eslint-disable` du code ; aucune règle n'est activée.
import reactHooks from "eslint-plugin-react-hooks";
import react from "eslint-plugin-react";

export default [
  {
    ignores: [
      "**/node_modules/**",
      "backend/**",
      "_vision_backup/**",
      "frontend/dist/**",
      "frontend/build/**",
      "frontend/public/**",
      "frontend/src/pages/legacy/**",
      "**/*.min.js",
    ],
  },
  {
    files: ["frontend/src/**/*.{js,jsx}"],
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
