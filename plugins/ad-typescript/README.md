# ad-typescript

TypeScript practices for Agentic Delivery: the `typescript-best-practices` skill, a hook that
reports ESLint findings after each edit, and, through the official `typescript-lsp` plugin that
installing this plugin also installs, a TypeScript language server for Claude.

## Install

```sh
/plugin marketplace add agentic-delivery-au/skills
/plugin install ad-typescript@agentic-delivery
```

## The TypeScript language server

Installing `ad-typescript` installs the official `typescript-lsp` plugin as a dependency. The plugin
gives Claude type diagnostics after each edit, and the `LSP` tool for go to definition and find
references.

The plugin needs `typescript-language-server` on your PATH. Claude Code looks on PATH only, not in
`node_modules/.bin`, so install it once per machine:

```sh
npm install -g typescript-language-server typescript
```

With nvm, a global install belongs to the active Node version. Install it under the version you
start `claude` from. Check with:

```sh
which typescript-language-server
```

Without it, Claude Code logs `Executable not found in $PATH` and works without the server.

`ad-typescript` requires `typescript-lsp`, so keep it enabled. `claude plugin disable` refuses to
disable `typescript-lsp` while `ad-typescript` is enabled. Claude Code does not load
`ad-typescript`, including the `typescript-best-practices` skill, if `typescript-lsp` cannot be
installed because the `claude-plugins-official` marketplace is unavailable. Only one language server
can handle `.ts` files, so do not enable a second TypeScript language server plugin alongside it.

The language server gives early feedback only. The repo's pre-commit and CI remain the gate.

## The ESLint hook

A `PostToolUse` hook on `Write`, `Edit` and `MultiEdit` runs
`npx --no-install eslint --max-warnings 0 --no-warn-ignored` on each `.ts`, `.tsx`, `.js`, `.jsx`,
`.mts`, `.cts`, `.mjs` or `.cjs` file Claude writes. If ESLint finds anything, the hook exits 2 with
the findings on stderr, so Claude fixes them in the same turn. It never touches your source: no
`--fix`, no Prettier, and nothing in an ESLint config can turn fixing on, because only the
command-line flag does. `--no-install` means npx never downloads a copy of ESLint.
`--no-warn-ignored` keeps a file your ESLint config ignores, or has no config for, from being
reported as a warning that `--max-warnings 0` would turn into a failure.

It needs `jq` and `npx` on your PATH, and ESLint in the project, for example
`npm install --save-dev eslint`. Without a project ESLint, npx falls back to a global `eslint`,
whose version and rules may differ from the gate's, or, with none, Claude sees npx's error after
each edit instead of findings. Rules that use type information make ESLint build a TypeScript
program on every run, so the hook takes a few seconds on each edit, and longer in a large project.
The hook gives early feedback only; the repo's pre-commit and CI remain the gate.

The hook says when it cannot run, and stays out of projects that are not Node projects:

- The project root (`$CLAUDE_PROJECT_DIR`, else the current directory) is resolved once to an
  absolute physical path, so a relative or trailing-slash `$CLAUDE_PROJECT_DIR` and symlinks in the
  root or the edited file's path all work. A root that does not exist is not a project. Only a
  `package.json` at that root turns the hook on, and npx runs from it. Without one it does nothing
  and exits 0, whatever the file, and needs no `jq`. A monorepo with `package.json` files only in
  subdirectories gets no lint from this hook, and in one that installs ESLint only in a package, a
  root `package.json` makes npx report that it cannot find ESLint after each edit.
- The edited file is resolved the same way: a relative path is read against the directory Claude was
  running in, then its directory is resolved physically, so `..` and symlinks are followed. A file
  outside the project root, such as a scratch file in `/tmp`, or in a directory that does not exist,
  is skipped, because ESLint 10 would fail it for having no config.
- In a project with a `package.json`, if `jq` is not on your PATH and the edited file is one of the
  extensions above, it prints one line to stderr and exits 1. That is a non-blocking error, which
  Claude Code shows, so a missing `jq` is not mistaken for a clean file. Other files are skipped
  silently.
- In a project with a `package.json`, if `npx` is not on your PATH and the edited file is in the
  project, it prints one line to stderr and exits 1, so a missing `npx` is not mistaken for a clean
  file.

The hook has no "could not enter the project root" outcome in practice: it resolves the root by
entering it, so a root it cannot enter is skipped as not a project. The script keeps a guard on the
final `cd` that exits 1, but it is unreachable short of the directory changing mid-run.

`--no-warn-ignored` needs flat config: ESLint 9 or later, or ESLint 8.57 or later with an
`eslint.config.*` file. On an older ESLint, or one using `.eslintrc.*`, ESLint rejects the option,
and Claude sees `Invalid option '--no-warn-ignored'` after each edit instead of findings. ESLint 10
looks for its config from the edited file's directory, but ESLint 9 looks from the working
directory, which the hook sets to the project root, so on ESLint 9 a repo with an `eslint.config.*`
in each package and none at the root fails after every edit.
