# Agentic Delivery skills

A Claude Code plugin marketplace: the development skills Agentic Delivery uses across client work,
collected so the same standards travel between repositories instead of being re-explained in each
one. Skills are grouped into plugins by what you are working on, and installed a plugin at a time.

MIT ([LICENSE](LICENSE)), covering this repository's own content.

## Install

```bash
claude plugin marketplace add agentic-delivery-au/skills
claude plugin install ad-general@agentic-delivery
```

Inside a session the same thing is `/plugin marketplace add agentic-delivery-au/skills`. A plugin is
named `<plugin>@agentic-delivery` wherever a name is asked for — installing, enabling, or
`enabledPlugins` in `.claude/settings.json`. `claude plugin marketplace update agentic-delivery`
picks up skills added since.

## The plugins

- **`ad-general`** — engineering practices that apply to any codebase, whatever the language. Holds
  `writing-comments`.
- **`ad-product`** — defining what to build and why. Holds `writing-prds`, which brings its own PRD
  template.

A skill is a `SKILL.md` under a plugin's `skills/`. The `description` in its front matter is what
decides when an agent reaches for it, so it is written for the moment it should fire rather than as
a summary of what it contains.

## Adding a skill

`plugins/<plugin>/skills/<skill>/SKILL.md`, with `name` matching the directory. Anything the skill
needs to read — a template, reference notes — goes beside it under `references/`, because whoever
installs the plugin gets that directory and nothing else, and a link climbing out of it resolves
only here.

A new plugin needs more than a directory: an entry in `.claude-plugin/marketplace.json`, its own
`.claude-plugin/plugin.json`, a package entry in `release-please-config.json` with a matching line
in `.release-please-manifest.json`, and its own `skill-validator` entry in `.pre-commit-config.yaml`
— that validator looks one level deep, so one entry per plugin. The hooks catch most of these. Keep
the plugin list above honest while you are here.

`AGENTS.md` has the rules the hooks enforce, and the hooks themselves are in
`.pre-commit-config.yaml`.

## Working in this repo

```bash
pre-commit install   # one-time, sets up the pre-commit and commit-msg hooks
```

- **mdformat** formats Markdown and wraps prose at 100 columns (see `.mdformat.toml`).
- **commitizen** enforces [Conventional Commits](https://www.conventionalcommits.org/) with a
  72-character subject limit.

### Repository settings

Already applied here, and recorded because settings are the part a clone does not carry. "Use this
template" copies files and nothing else, so this repo started with no branch protection and merge
settings at GitHub's defaults. `scripts/bootstrap_repo.py` applies them, and re-running it reports
what has since drifted. It prints a plan and changes nothing until you pass `--apply`.

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

The App is installed and its credentials are set at the organisation, so this repo releases. The
steps below are what a repo without it needs, and there is deliberately no fallback to
`GITHUB_TOKEN` — a silent downgrade would reintroduce the unmergeable release PR — so a repo missing
either credential fails at the token step on every push to `main`.

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

Each plugin is versioned on its own. [release-please](https://github.com/googleapis/release-please)
reads the Conventional Commits landed on `main`, attributes each to the plugin whose files it
touched, and keeps a release pull request open per plugin. Merging one tags that plugin and
publishes its GitHub release, leaving the others where they are.

The version that matters is the one a marketplace consumer reads, `version` in the plugin's
`.claude-plugin/plugin.json`. `release-please-config.json` has a package entry per plugin path
pointing at it with `extra-files` and a jsonpath, and `.release-please-manifest.json` records where
each plugin has got to. A changelog is written beside the plugin it describes, not at the root, and
a tag carries the plugin's name: `ad-general-v0.2.0`.

Plugins start at `0.1.0` and a feature bumps the minor, so a version says what changed without
claiming the skills have settled. `1.0.0` is a decision to make per plugin, not a default to arrive
at by accident.

Two things follow from releasing per plugin. A commit that touches nothing under `plugins/` belongs
to no plugin, so hook changes, scripts, workflows and this README appear in no changelog and trigger
no release. And each plugin still carries a `version.txt` updater it has no file for, so every run
logs `file plugins/<name>/version.txt did not exist` — harmless, and the reason nothing here creates
one.

Adding a plugin means adding its entry to both files. Nothing about a release would fail if you
forgot — the plugin would simply never release, sitting at whatever version it was created with — so
the manifest check fails the commit instead, and it also fails an entry that releases without
bumping `plugin.json` or without a component to tag.

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
`LICENSE`, `SECURITY.md` and the release config are simply not listed, and `.github/CODEOWNERS` and
`.github/dependabot.yml` are excluded from `.github` explicitly. The template's version of each
holds a placeholder or a language choice, never something to adopt — and where this repo has dropped
the file outright, as it has for `CODEOWNERS` and `version.txt`, a refresh should not offer it back.

A hook rev that is newer downstream is not drift. `pre-commit autoupdate` is how it is meant to be
bumped; a repo that is ahead should stay ahead, and the template should catch up.
