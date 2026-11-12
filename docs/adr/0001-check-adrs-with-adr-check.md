---
status: accepted
date: "2026-11-13"
supersedes: []
superseded_by:
---

# 0001. Check ADRs with adr-check

> In the context of keeping architecture decision records (ADRs) in this repo, facing records that
> drift from their format and merged decisions that get rewritten, we decided for running
> [adr-check](https://github.com/agentic-delivery-au/adr-check) in a pre-commit hook and in CI and
> neglected review alone, to achieve uniform records that stay put once merged, accepting that CI
> must stay in step with the hook's pinned version.

## Context

This repo records its decisions as ADRs in `docs/adr/`. An ADR is only useful if a reader can trust
its format and trust that a merged one still says what the team decided then. Nothing in the repo
checks either.

`adr-check` checks the format of every ADR: filename, frontmatter, title, sections and supersession
links. With `--mode ci` it also compares a branch with a base ref. It rejects an edit to a merged
ADR, a deletion, a rename and a reused number, and with `--merging-to-main` it rejects `proposed`.
It is published to PyPI as `adr-check` and runs through `uvx`.

A pre-commit hook sees only the working tree, so it cannot catch a change to a merged ADR. A hook
can also be skipped locally, while CI runs on every pull request whatever the author's machine does.

## Considered options

### Run adr-check in a pre-commit hook and in CI

- Good: the hook gives early feedback on format, and CI catches what the hook cannot see.
- Good: the same tool and version apply locally and in CI.
- Bad: two places pin the version and must be bumped together.
- Bad: `uvx` has to be installed locally for the hook.

### Run adr-check in CI only

- Good: one place to pin the version, and no local setup.
- Bad: a format error surfaces only after a push.

### Review alone

- Good: no tooling to maintain.
- Bad: a reviewer has to notice a quietly edited merged ADR, and does not always.

## Decision

We will run `adr-check` as a `pre-commit` hook over `docs/adr/`, and as a `pull_request` and `push`
workflow in CI. A pull request is compared with its base branch
(`--mode ci --base-ref origin/<base>`), with `--merging-to-main` added when that base is `main`. A
push to `main` runs only the checks on the files, with no comparison.

We will pin the same version in `.pre-commit-config.yaml` and `.github/workflows/adr-check.yml`, and
bump them together.

We will write ADRs to the format `adr-check` expects. An ADR on a branch may be `proposed`, and must
be `accepted` or `rejected` before it merges to `main`.

## Consequences

- A malformed ADR fails at commit time, and an edit to a merged ADR fails in CI.
- The `adr-correction` label is the one way to fix a typo in a merged ADR's body.
- Contributors need `uvx` for the hook to run locally.
- The two version pins can drift. Each carries a comment pointing at the other.
- The workflow checks out full history, so it costs more than a shallow checkout.
