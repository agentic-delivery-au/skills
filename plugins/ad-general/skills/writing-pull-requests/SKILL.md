---
name: writing-pull-requests
description: Use when about to write or revise a pull request description, when a description is growing into a summary of the diff or a restatement of the issue, or when deciding whether a change needs a description at all.
---

# Writing Pull Requests

This governs the **description** — the body of a pull request. The title is a different artefact
with different rules, and under squash merge it is also the commit subject.

## The one rule

**The issue holds the substance. The description says what the issue and the diff do not.**

A reviewer arrives having read the issue and about to read the diff. Everything written here
competes with those two and loses to both. What survives is small and worth having.

Substance belongs in the issue because it is findable before the work starts, it outlives the
branch, and it is where disagreement is cheap. By the time there is a diff, the argument is
expensive.

## The two failures

Both read as thoroughness. Both cost the reviewer time.

**Re-stating the issue.** From this repository. The issue:

> `LICENSE` is the template's placeholder: it says a licence has not been chosen and grants nothing.
> […] visible is not the same as usable.

The description of the pull request that closed it:

> `LICENSE` was the base template's placeholder: it stated that no licence had been chosen and
> granted nothing to anyone. […] visible is not the same as usable.

The same paragraph, retyped in the past tense, down to the closing clause. The reviewer had already
read it. `Fixes: #2` was the whole job.

**Restating the code.** The files changed are listed above the description, and the diff is one
click away. A description that walks through them adds a second, staler copy.

## The test

For each paragraph, heading and bullet: **would a reviewer who has read the issue and the diff learn
anything from this?**

If no, cut it. This catches the two failures above, and it catches process narration — the urge to
explain comes from having just done the work, and the reader has not.

It also catches the shapes that make a short description look long: a heading standing over one
sentence, a bullet list whose items are not a list, and a paragraph answering an objection nobody
has made. Each is formatting doing the work that substance should.

## What earns space

- **Evidence it works.** The thing the diff cannot show.
- **A surprise.** Anything in the diff that would make a reviewer stop, guess wrong, or object.
- **A decision with an alternative.** Where an obvious other route was rejected, one line on why,
  because the reviewer will otherwise suggest it.
- **A consequence outside the diff.** A setting to change, an ordering against another PR, something
  that must happen before or after merge.

Nothing else. A change where none of these apply needs no prose — the title and the diff have
already said it. What a repository requires is not prose and still applies: an issue reference, the
fields of a pull request template, a trailer. Leave those; drop the paragraphs around them.

## Evidence, not process

"Ran the tests" is process. The output is evidence. But paste the smallest thing that carries it:

| Instead of                            | Write                                              |
| ------------------------------------- | -------------------------------------------------- |
| Twenty lines of a passing check suite | `pre-commit run --all-files` — all pass            |
| "Tested manually"                     | What was run, and what it printed                  |
| "Added tests"                         | The case that would have failed before this change |

A wall of green is not evidence. It is a screenshot of a green light, and it buries the one line
that mattered.

## Proportionate is not short

A change that alters an interface, makes an irreversible decision, or turns out to rest on something
counter-intuitive earns its paragraphs. The test is never the size of the diff — a one-line change
can need three paragraphs and a thousand-line rename can need none.

## Where squash merge is used

The description becomes the commit body, permanent and reachable from `git blame`. Write it for
someone reading `git log` in a year, who has the diff and no browser tab open.

## Override

If someone asks for a detailed write-up, write one. This governs the default.
