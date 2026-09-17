// Config ESLint (ESLint 9) pour le frontend — sans import externe.
// Stubs no-op pour les règles référencées par des directives eslint-disable.
const stub = (names) => ({
  rules: Object.fromEntries(names.map((n) => [n, { create: () => ({}) }])),
});

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
