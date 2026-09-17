// Config ESLint racine (ESLint 9). AUCUN import externe (robuste quel que soit
// le cwd d'exécution). On déclare des stubs no-op pour les règles référencées
// par des directives `eslint-disable` dans le code, afin qu'ESLint ne lève pas
// « Definition for rule ... was not found ». Aucune règle n'est réellement activée.
const stub = (names) => ({
  rules: Object.fromEntries(names.map((n) => [n, { create: () => ({}) }])),
});

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
    plugins: {
      "react-hooks": stub(["exhaustive-deps", "rules-of-hooks", "set-state-in-effect"]),
      react: stub(["no-unknown-property", "no-unescaped-entities", "jsx-key", "display-name", "prop-types", "no-children-prop"]),
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    linterOptions: { reportUnusedDisableDirectives: "off" },
    rules: {},
  },
];
