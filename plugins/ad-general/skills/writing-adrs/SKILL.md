---
name: writing-adrs
description: Writes, supersedes, consults and reviews architecture decision records (ADRs) in a repository's docs/adr/ directory. Use when a change is hard to reverse, picks between real alternatives, or constrains other repos or teams; before any architectural change; when replacing an earlier decision; or when reviewing any pull request, to ask whether it needs an ADR.
---

# Writing ADRs

An architecture decision record (ADR) is a short file that records one decision: its context, the
options considered and the consequences. The code shows what was built. The ADR shows why, for the
person who arrives later and has only the file.

The template is [`references/ADR-template.md`](references/ADR-template.md). Read it before you
write. This file governs how to fill it in, and how to read and review ADRs.

An ADR is not a design doc. A design doc explores how to build something and expires once the work
merges. An ADR records one choice and lasts. A design doc may lead to one or more ADRs. If the
`writing-design-docs` skill is available, use it for the exploration.

For files in `docs/adr/`, this skill's template and rules govern over any other skill's ADR format.
The formats differ, and an ADR in the other format fails the check.

## Consult before you change

Before an architectural change, read the ADRs in `docs/adr/`. An agent that skips them can act on a
decision the team has reversed, or undo a reversal.

- `accepted` is in force. Follow it.
- `superseded` and `rejected` are not in force. For a superseded one, follow `superseded_by` to the
  ADR that replaced it, and read that instead.
- `proposed` is under review on a branch. It binds nobody yet. One already on `main` binds nobody
  either, and only a person can settle it (see Supersede).

If your change conflicts with an accepted ADR, do not work around it and do not edit it. Propose a
superseding ADR, and say so to the person you are working for. A person owns the decision.

## Write

Write an ADR when a decision meets any one of three tests:

1. **Hard to reverse.** Walking back costs real time, money or data.
1. **Picks between real alternatives that someone could reopen.** A reasonable colleague could
   propose the other option next year.
1. **Constrains other repos, teams or platforms.** Other people must follow the choice.

Anything else belongs in the PR description or the code. A minor dependency bump, a function name
and a field on one object do not need an ADR. When in doubt, write a short one: ten lines of Context
and Decision cost less than the argument next year.

One decision per ADR. If you write "and also we decided", split it into two files, give each its own
number and link them in the Context. One decision means one status, so you can supersede one without
touching the other.

1. **Number it.** Take the next free number in this repo's `docs/adr/`, starting at 0001. Look at
   the directory, not your memory. Never reuse a number, even for a rejected or superseded ADR.
1. **Name it.** `docs/adr/NNNN-kebab-title.md`: four digits, then lowercase words joined by hyphens.
   The H1 repeats the number: `# 0007. Use managed identities`.
1. **Fill the template.** Keep the four frontmatter keys and the four sections, in order. The
   frontmatter has no ticket key, because the PR that adds the ADR links its ticket. Link the ADR
   from the ticket too.
1. **Set `status: proposed`.** The PR is where the team decides, so a new proposal's decision has no
   date yet. Write today's date as a placeholder, because the check needs an ISO date, and replace
   it with the date the team made the decision when you set the final status. Keep it only if the
   team decided that day. A retroactive ADR is different: it already carries the original decision
   date, which stays.

Write each section for what it is:

- **Context** states the situation, constraints and pressures, and does not argue for the answer.
- **Considered options** lists only the options the team weighed, each with pros and cons, the
  chosen one included. Never invent one to flatter the choice.
- **Decision** uses full sentences beginning "We will ...".
- **Consequences** lists what follows, good and bad. A list of only good ones is an advertisement.

The optional Y-statement sits under the H1: "In the context of X, facing Y, we decided for Z and
neglected W, to achieve V, accepting that U". Use it when a reader would want the answer without the
argument.

### From proposal to record

`proposed` belongs only on a branch. One that reached `main` anyway is covered under Supersede. The
person reviewing the PR makes the decision, and you set the final status before it merges:
`accepted`, `rejected` or `superseded`. At the same time, set `date` to the date the team made the
decision, unless the ADR is retroactive. Never merge `proposed`.

If the team decides against the proposal, set `status: rejected`, keep the reasoning in Context and
Considered options, and merge it as a record. Remove the proposed change from the PR, so only the
rejected ADR merges. If it would have superseded an ADR, leave that ADR untouched, empty
`supersedes`, and name the ADR in the Context. To revive a rejected option later, write a new ADR
and name the rejected one in its Context, not in `supersedes`.

### Recording a decision after the fact

A retroactive ADR records. It must not justify.

- Set `date` to the original decision date. If unknown, use the earliest date it is visible, such as
  the first commit or ticket, and say in the Context that the date is approximate and where it came
  from.
- Begin the Context with "Recorded retrospectively".
- List only the options the team considered at the time.
- If the reasons were not recorded and nobody remembers them, say that. It beats a plausible guess.
- Link the ticket or commit where the decision was made.

## Supersede

An accepted ADR records what the team decided and why, at the time. Rewriting it to match new
reality destroys that. Change a decision by writing a new ADR:

1. Write the new ADR with `supersedes: [N]`, where N is the old ADR's number.
1. In the old ADR, change `status` to `superseded` and set `superseded_by` to the new number.
1. Land both in the same PR.

Leave the rest of the old ADR alone. Never edit the body of an accepted, rejected or superseded ADR.
Three edits are allowed:

- **The supersession flip** above: `status` and `superseded_by` only.
- **A correction**: a typo or a broken link, fixed on a PR labelled `adr-correction`. You apply the
  label. A correction changes no frontmatter and leaves the meaning as it was. A PR labelled
  `adr-correction` is still reviewed like any other change, however small the fix. Repointing a link
  is a correction. Changing "we will use" to "we will not use" is a change, and needs a new ADR.
- **The renumbering repair.** If two ADRs share a number on `main`, the later-merged one is
  renumbered. The repair changes only that ADR's filename, its H1 number, and the `supersedes` and
  `superseded_by` numbers that point at it. Decide by hand which ADR each of those numbers meant.

An ADR still `proposed` on `main` is one more exception. It got there before the repo adopted the
check, or past a failing check the repo does not require. Until it is settled, it fails the check on
every PR into `main`, including PRs that never touch it. Only a person decides its final status.
Never set one yourself to clear the check: tell the person you work for. Once they decide, settle it
in a PR that sets the final status and date, and review that PR as you would a new ADR, because the
check lets its body and frontmatter change. If it supersedes another ADR and the person rejects it,
no PR can pass the check: the older ADR would have to return to `accepted`, and the check forbids
that edit. Do not merge past the failure and leave the older ADR superseded by a rejected one. Tell
the person, who decides how to repair it.

Do not delete or rename an ADR, other than by the renumbering repair: tickets and other ADRs link to
its number and name. To retire a decision with no replacement, write an ADR that records the
retirement and supersedes the old one. Do not use `deprecated`.

## Review

Ask these questions in addition to the usual review. Each bullet names the PRs it applies to. The
first two apply when the PR adds an ADR, settles one still `proposed` on `main`, or carries
`adr-correction`. The third applies to every PR, because a decision made without its ADR shows only
in the diff of the PR that makes it.

- **On any PR that adds or settles an ADR:** do Considered options and Consequences match the choice
  in Decision? The chosen option must appear in Considered options. Its pros and cons must agree
  with the listed Consequences. A Decision that no option supports, or a Consequences list that
  describes a different choice, means the record is wrong.
- **On a PR labelled `adr-correction`:** is the change to the accepted ADR only a typo or a link
  fix, with its meaning unchanged? If it shifts the meaning, reject the label and ask for a
  superseding ADR. The label switches off the script's check of the body, so the script cannot block
  a mislabelled change; the reviewer reading the diff has to.
- **On every PR, whether or not it touches `docs/adr/`:** does the change make an architecturally
  significant decision that needs an ADR? Apply the three tests in Write: the decision is hard to
  reverse, picks between real alternatives someone could reopen, or constrains other repos, teams or
  platforms. If it meets any one, does the PR add the ADR? A decision with no ADR in the PR that
  makes it is a finding.

## What the ADR check enforces

Repos run one script, [adr-check](https://github.com/agentic-delivery-au/adr-check), as a pre-commit
hook and in CI. Write ADRs that pass it. The hook runs the checks that need only local files. CI
runs those and the checks that need `main`.

In both places:

- The filename matches `NNNN-kebab-title.md`.
- The frontmatter parses, has `status`, `date`, `supersedes` and `superseded_by`, uses an allowed
  `status` and an ISO `date`.
- The H1 number matches the filename number.
- Context, Considered options, Decision and Consequences are all present.
- Every number in `supersedes` names an ADR that is `superseded` and names this one back in
  `superseded_by`. Every `superseded` ADR is named in its successor's `supersedes`.
- No two ADRs share a number.

In CI only:

- No number duplicates one already on `main`. If another PR took your number first, renumber yours.
- The body of an ADR on `main` is unchanged, whatever its status. Only `accepted` to `superseded`,
  together with `superseded_by`, is allowed. `adr-correction` lifts the body rule alone. The
  renumbering repair is another exception, to the body and rename rules. An ADR already `proposed`
  on `main` is exempt from the body and frontmatter rules, so it can be settled.
- No ADR is deleted or renamed, except by the renumbering repair.
- No ADR with `status: proposed` reaches `main`.

Never skip a hook. Fix an ADR your change adds or proposes until it passes. Edit an ADR already on
`main` only by the three edits under Supersede: the supersession flip, a correction or the
renumbering repair. The one other edit is settling an ADR still `proposed`, on a person's decision.
Never make any other edit to it to satisfy the check.
