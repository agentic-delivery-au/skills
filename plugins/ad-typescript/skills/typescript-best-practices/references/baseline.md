# The baseline ESLint and TypeScript configuration

This is Agentic Delivery's baseline ESLint and TypeScript configuration, taken from
[`agentic-delivery-au/typescript-simple-template`](https://github.com/agentic-delivery-au/typescript-simple-template),
for a project to copy. Change the project-specific values (the Next.js plugin block, the `paths`
alias, `include`, `jsx`, `lib` and `module` if the project is not a Next.js app) to the project's
own and leave the rest. The statements in `SKILL.md` and `patterns.md` about `no-console`, the
suppression rules, `no-explicit-any` and the `no-unsafe-*` rules, the `_exhaustive` local, `strict`
and Prettier are claims about these files; a change to the rule selection or the compiler options is
a change here. Comments in the template that cite an engineering standard outside this repository
are reworded below.

## `eslint.config.mjs`

```js
import comments from "@eslint-community/eslint-plugin-eslint-comments";
import js from "@eslint/js";
import nextPlugin from "@next/eslint-plugin-next";
import { defineConfig } from "eslint/config";
import prettier from "eslint-plugin-prettier/recommended";
import n from "eslint-plugin-n";
import tseslint from "typescript-eslint";

export default defineConfig([
  { ignores: [".next/**", "node_modules/**", "out/**", "coverage/**", "next-env.d.ts"] },

  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      // Prettier last: it switches off the ESLint rules that would fight the formatter.
      prettier,
    ],
    // only-throw-error needs type information. tsconfig.json includes tests/, so
    // the project service covers every linted file and no second tsconfig is needed.
    languageOptions: {
      parserOptions: { projectService: true },
    },
    rules: {
      // Deviations from typescript-eslint's recommended config
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/explicit-module-boundary-types": "error",
      "@typescript-eslint/ban-ts-comment": [
        "error",
        {
          "ts-expect-error": "allow-with-description",
          "ts-ignore": true,
          "ts-nocheck": true,
          minimumDescriptionLength: 10,
        },
      ],

      // Additions
      "no-console": "error",
      "@typescript-eslint/only-throw-error": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },

  // The Node-environment rules, narrowed. eslint-plugin-n's `recommended-module` config
  // assumes a Node runtime; in typescript-simple-template roughly half the code runs in a
  // browser, where those rules report against globals that genuinely exist. Only the
  // two rules that hold on both sides are enabled.
  {
    files: ["**/*.{ts,tsx,mjs}"],
    plugins: { n },
    rules: {
      "n/prefer-node-protocol": "error",
      // Read env through a typed config module instead.
      "n/no-process-env": "error",
    },
  },

  // Where that config module goes when the app needs one: the single place
  // allowed to touch process.env.
  {
    files: ["**/config.ts"],
    rules: { "n/no-process-env": "off" },
  },

  // Next's own rules. In typescript-simple-template, deliberately not eslint-config-next,
  // which pins react, jsx-a11y and import plugin versions that fail on ESLint 10.
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: { "@next/next": nextPlugin },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
    },
  },

  // Suppression discipline. Applies to every linted file.
  {
    plugins: { "@eslint-community/eslint-comments": comments },
    rules: {
      "@eslint-community/eslint-comments/no-unlimited-disable": "error",
      "@eslint-community/eslint-comments/require-description": "error",
    },
  },
]);
```

## `tsconfig.json` compiler options

```jsonc
{
  "compilerOptions": {
    // ES2024 is what Node 24 and current browsers run natively, so nothing is
    // downlevelled that the runtime already understands.
    "target": "ES2024",
    // Browser globals, which a Node-only project leaves out.
    "lib": ["dom", "dom.iterable", "ES2024"],
    // esnext/bundler rather than NodeNext: in typescript-simple-template Next resolves
    // and bundles the imports itself, and NodeNext makes it fail to build.
    "module": "esnext",
    "moduleResolution": "bundler",
    "verbatimModuleSyntax": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "skipLibCheck": true,
    // In typescript-simple-template Next owns emit, so there is no tsconfig.build.json.
    "noEmit": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    },
    "allowJs": true
  }
}
```

The template's `include` lists `src`, `tests`, `e2e`, `*.config.ts` and Next's generated types.
`tests/` is there on purpose: leave it out and the type-aware lint rules fail in it with "was not
found by the project service", which is what forces the extra `tsconfig.eslint.json` some
repositories carry.

The template pins Node 24 (`engines`, `.nvmrc`), TypeScript 6.0.3 and ESLint 10.14.0, and its
`package.json` scripts run the gate as `eslint . --max-warnings 0`, `tsc --noEmit` and
`prettier --check .`. Its `.pre-commit-config.yaml` runs the same tools through `npx --no-install`,
so the versions match CI. `defineConfig` from `eslint/config` needs ESLint 9.22 or later.
