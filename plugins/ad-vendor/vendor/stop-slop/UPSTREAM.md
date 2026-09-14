# Upstream

The skill at `../../skills/stop-slop/` is vendored, not written here. Every file in that directory
is upstream's. Do not edit them.

| | |
| --- | --- |
| Source | <https://github.com/hardikpandya/stop-slop> |
| Author | Hardik Pandya, <https://hvpandya.com> |
| Licence | MIT, see `LICENSE` beside this file |
| Vendored at | commit `8da1f03`, committed 17 Mar 2026; taken 14 Sep 2026 |
| Files | `SKILL.md` and the three files under `references/` |

Upstream is not installable as a plugin: it is a `SKILL.md` at a repository root, with no manifest
and no `skills/` directory, so a marketplace entry pointing at it installs nothing. The wrapper
around it is the whole reason these files are copied rather than pinned. See
agentic-delivery-au/skills#9 for when to pin instead.

## Why the licence and this file are not in the skill directory

A skill directory should hold only what an agent should read, because everything in it can be
loaded into a context window. `LICENSE` and this file are 742 tokens that help a maintainer and do
nothing for the task, and `skill-validator` fails a skill that carries them. They stay inside the
plugin, which is the unit that gets distributed, so the notice still travels with the copy.

## Updating

Pick the ref you want and fetch it. Using a commit rather than `main` means the table above always
describes what is actually on disk, and re-running it later reproduces the same files.

```bash
REF=$(gh api repos/hardikpandya/stop-slop/commits/main --jq .sha)   # or a specific commit
BASE="https://raw.githubusercontent.com/hardikpandya/stop-slop/$REF"
SKILL=plugins/ad-vendor/skills/stop-slop
for f in SKILL.md references/phrases.md references/structures.md references/examples.md; do
  curl -sS --fail "$BASE/$f" -o "$SKILL/$f"
done
curl -sS --fail "$BASE/LICENSE" -o plugins/ad-vendor/vendor/stop-slop/LICENSE
echo "$REF"
```

Record that commit in the table above, and check `SKILL.md` for new files under `references/`
before assuming the list is still complete.

## Why it is exempt from the formatters

`.mdformat.toml` and `.markdownlintignore` both exclude `plugins/ad-vendor/`. mdformat rewrites 263
lines across the four upstream files, and once it has, the copy no longer diffs against upstream,
which turns every update into a manual merge. That is how a vendored copy quietly stops being
updated.

The exemption covers this file too, so keep it at 100 columns by hand.

Changes wanted in the skill belong upstream as a pull request, not as a local edit.
