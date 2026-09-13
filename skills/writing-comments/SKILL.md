---
name: writing-comments
description: Use when about to write a code comment, when a change adds explanatory comments, or when deciding whether an existing comment should survive an edit.
---

# Writing Comments

This governs **comments** — the inline explanation beside code, `//`, `#`, `/* */`. A docstring or
API doc block is a different artefact with a different reader, and nothing here applies to it.

## The default is none

Write no comment. A comment must justify its existence, and the absence of one is the right answer
almost always.

## What justifies one

The **why** is non-obvious, and a future reader would otherwise be confused or break the code:

- **A hidden constraint** — `API requires this header lowercased; the server rejects mixed case`
- **A subtle invariant** —
  `must run before the widget mounts, or the listener binds to the wrong target`
- **A workaround** — `Safari 17 fires focus twice; debounce`
- **Behaviour that would surprise a competent reader of this code**

One line. Two at most.

## What does not

| Comment                                                                        | Why not                                                      |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| Restates what the code does                                                    | The identifier already says it                               |
| Narrates the change or its origin — `added to fix #123`, `previously called Y` | Belongs in the PR description, and rots as the code moves on |
| Section headers inside a function body — `# --- validation ---`                | If a function needs sections it needs splitting              |
| Restates a type annotation or signature                                        | The signature is right there and stays true                  |
| `TODO` with no tracked issue                                                   | Either fix it now or file it; drift markers accumulate       |
| Commented-out code                                                             | Delete it. Git remembers                                     |

## The test

Before writing one, ask: **would removing this confuse a future reader who knows nothing about the
task I am doing right now?**

If no, do not write it. That question is the one that catches change-narration, because the urge to
explain comes from having just done the work — and the reader will not have.

## Editing code that already has comments

Redundant comments touching the lines you are changing are fair game to remove. Do not open a
comment-stripping pass across files the task did not touch.

## Override

If someone explicitly asks for verbose or teaching comments, write them. This governs the default,
not their instruction.
