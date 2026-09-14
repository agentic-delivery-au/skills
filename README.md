# base-template

The base template every new repository is created from (GitHub's "Use this template"). It sets up
the tooling and conventions that apply regardless of language:

- **pre-commit** — hook config in `.pre-commit-config.yaml`, run in CI on every PR.
- **Markdown formatting** — [mdformat](https://mdformat.readthedocs.io), configured in
  `.mdformat.toml`.
- **Markdown linting** — [markdownlint](https://github.com/igorshubovych/markdownlint-cli),
  configured in `.markdownlint.jsonc`.
- **Conventional Commits** — enforced by commitizen via the `commit-msg` hook.
- **Secret scanning** — [betterleaks](https://github.com/betterleaks/betterleaks), configured in
  `.betterleaks.toml`.
- **Consistent line endings** — `.gitattributes` normalizes text files to LF on checkout.
- **Editor defaults** — [.editorconfig](https://editorconfig.org) gives editors the same whitespace
  rules the hooks enforce, so files arrive conforming.
- **PR conventions** — a PR template and a title-lint workflow, both under `.github/`.
- **Releases** — [release-please](https://github.com/googleapis/release-please), configured in
  `release-please-config.json` and `.release-please-manifest.json`. See [Releases](#releases) for
  what a new repo has to change.
- **License** — [MIT](LICENSE). Covers this repository's own content; a vendored third-party skill
  keeps the licence it came with.
- **`AGENTS.md`** — the starting rules for an AI agent working in a new repo, read by any agent that
  supports the convention. `CLAUDE.md` is a one-line pointer to it, kept only so Claude Code finds
  it.

Language-specific templates (Python, React, ...) are created from this one and add their own
language tooling on top; they should not need to redo anything listed above.

## Setup

```bash
pre-commit install   # one-time, sets up the pre-commit and commit-msg hooks
```

- **mdformat** formats Markdown and wraps prose at 100 columns (see `.mdformat.toml`).
- **commitizen** enforces [Conventional Commits](https://www.conventionalcommits.org/) with a
  72-character subject limit.

### Repository settings

"Use this template" copies files and nothing else, so a new repo starts with no branch protection,
merge settings at GitHub's defaults, and the Actions permission release-please needs to open its
release PR switched off. `scripts/bootstrap_repo.py` applies them. It prints a plan and changes
nothing until you pass `--apply`.

Read the plan before applying it. An existing ruleset is replaced wholesale, so the plan diffs the
repo's policy against the template's: a `-` line is policy this repo has and the template does not,
and applying loses it. A repo that has added its own required check will see it there.

The diff covers every field the template states. A ruleset field the template says nothing about
reverts to GitHub's default when the ruleset is replaced, and the plan cannot show that.

```bash
python3 scripts/bootstrap_repo.py            # what it would change
python3 scripts/bootstrap_repo.py --apply    # change it
```

### Release bot (GitHub App)

`release-please.yml` authenticates as a GitHub App rather than with `GITHUB_TOKEN`, because a pull
request opened with `GITHUB_TOKEN` triggers no workflows: the checks the ruleset requires would
never report on the release PR, and it could never merge.

**Do this before merging anything that runs the workflow.** There is deliberately no fallback to
`GITHUB_TOKEN` — a silent downgrade would reintroduce the unmergeable release PR — so until the App
exists and both credentials are set, every push to `main` fails at the token step.

1. Create the App under the organisation: Settings → Developer settings → GitHub Apps → New. It
   needs no webhook and no callback URL.
1. Grant it exactly three repository permissions: **Contents** write, **Issues** write, **Pull
   requests** write. Nothing else.
1. Install it (App settings → Install App) on the repositories that cut releases.
1. Generate a private key (App settings → Private keys) and download the `.pem`.
1. Store both credentials on the repository, under Settings → Secrets and variables → Actions:
   `RELEASE_BOT_CLIENT_ID` as a **variable**, and `RELEASE_BOT_PRIVATE_KEY` as a **secret** holding
   the whole `.pem`, `BEGIN` and `END` lines included.

The token is narrowed three times over, and the middle one is the one that gets missed:

- The App's own permissions are the ceiling. It can never mint a token holding more than the three
  granted in step 2, whatever a workflow asks for.
- `permission-contents`, `permission-issues` and `permission-pull-requests` on the token step narrow
  each run to release-please's documented minimum. Omit them and the token inherits **every**
  permission the installation holds — the ceiling becomes the grant.
- No `owner` or `repositories` input, so the token reaches only the repository running the workflow.
  The action revokes it when the job finishes, and it expires within the hour regardless.

`permissions: {}` at the top of the workflow then leaves `GITHUB_TOKEN` itself with nothing, since
the App token does all the work.

## Releases

[release-please](https://github.com/googleapis/release-please) reads the Conventional Commits landed
on `main` and keeps an open release PR that bumps the version and updates `CHANGELOG.md`. Merging
that PR tags the version and publishes the GitHub release.

The version that matters is the one a marketplace consumer reads, `version` in the plugin's
`.claude-plugin/plugin.json`. `release-please-config.json` points at it with `extra-files` and a
jsonpath, so a release bumps that field. There is no `version.txt` here: nothing read it.

A second plugin makes this repo a monorepo, and one shared version across independently useful
plugins stops being honest at that point. The
[manifest releaser docs](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
cover a package entry per plugin, and `"separate-pull-requests": true` for a release PR each.

## Keeping up with the template

"Use this template" copies the files once and keeps no link, so nothing here reaches a repo already
created from it. Picking up a later change is a manual diff, by choice: an automatic sync would have
to decide what to do about a hook version someone bumped or a section someone added, and getting
that wrong silently is worse than not having it.

To see what a repo is missing:

```bash
git remote add template https://github.com/agentic-delivery-au/base-template.git
git fetch template
git diff HEAD template/main -- .github .pre-commit-config.yaml AGENTS.md CLAUDE.md \
  .editorconfig .gitattributes .markdownlint.jsonc .markdownlintignore .mdformat.toml \
  .betterleaks.toml ':(exclude).github/CODEOWNERS' ':(exclude).github/dependabot.yml'
```

Read it as "what taking everything would do": `+` is what the template would add, and `-` is what it
would take away — your own edits, and any hook you have already bumped past the template. Take what
applies and leave the rest. Working from your own copy of the template rather than this one? Point
the remote at that copy.

The pathspec leaves out what is per-repo by design, so the diff stays worth reading: `README.md`,
`LICENSE`, `SECURITY.md`, the release config and `version.txt` are simply not listed, and
`.github/CODEOWNERS` and `.github/dependabot.yml` are excluded from `.github` explicitly. The
template's version of each holds a placeholder or a language choice, never something to adopt.

A hook rev that is newer downstream is not drift. `pre-commit autoupdate` is how it is meant to be
bumped; a repo that is ahead should stay ahead, and the template should catch up.
