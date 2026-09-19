import js from "@eslint/js";
import globals from "globals";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";
import importPlugin from "eslint-plugin-import";

export default [
  { ignores: ["node_modules/**", "dist/**", "build/**", "public/**", "src/pages/legacy/**", "plugins/**"] },
  js.configs.recommended,
  {
    files: ["src/**/*.{js,jsx}", "*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: { ...globals.browser, ...globals.es2021, ...globals.node },
    },
    plugins: { react, "react-hooks": reactHooks, "jsx-a11y": jsxA11y, import: importPlugin },
    settings: { react: { version: "detect" } },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "warn",
      "no-empty": ["warn", { allowEmptyCatch: true }],
      "no-useless-escape": "warn",
      "no-control-regex": "off",
      "no-async-promise-executor": "warn",
      "no-constant-condition": "warn",
      "no-dupe-keys": "warn",
      "no-fallthrough": "warn",
      "no-prototype-builtins": "warn",
      "no-redeclare": "warn",
      "no-unreachable": "warn",
      "use-isnan": "warn",
      "valid-typeof": "warn",
      "react/prop-types": "off",
      "react/react-in-jsx-scope": "off",
      "react/no-unescaped-entities": "off",
      "react/display-name": "off",
      "react-hooks/rules-of-hooks": "warn",
      "react-hooks/exhaustive-deps": "off",
      "react-hooks/set-state-in-effect": "off",
    },
  },
];
