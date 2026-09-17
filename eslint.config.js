// Config ESLint racine (ESLint 9). Autonome : aucun import externe.
// Des stubs no-op déclarent les règles référencées par les directives
// `eslint-disable` du code, pour éviter "definition not found". Aucune règle activée.
const stub = (names) => ({ rules: Object.fromEntries(names.map((n) => [n, { create: () => ({}) }])) });

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
    languageOptions: { ecmaVersion: "latest", sourceType: "module", parserOptions: { ecmaFeatures: { jsx: true } } },
    linterOptions: { reportUnusedDisableDirectives: "off" },
    rules: {},
  },
];
