---
status: proposed
date: "{{YYYY-MM-DD}}"
supersedes: []
superseded_by:
---

<!--
  ADR TEMPLATE

  File: docs/adr/NNNN-kebab-title.md. Four digits, lowercase words joined by hyphens.

  Replace every {{placeholder}}, including the braces (and the quotes around the date). Delete every
  guidance comment, this one included. Keep the four frontmatter keys and the four section
  headings, in this order.

  status: proposed on the branch. Before merge: accepted, rejected or superseded. Never proposed.
  date: the day the team made the decision, in ISO form. While proposed, today's date is a
  placeholder. Set the decision date when you set the final status. A retroactive ADR keeps its
  original decision date.
  supersedes: numbers of the ADRs this one replaces, as plain integers, for example [7]. Empty if
  none.
  superseded_by: number of the ADR that replaces this one. Empty until then.

  The H1 number must equal the filename number. One decision per file. A page or two.
-->

# {{NNNN}}. {{Title that names the decision}}

<!-- Optional Y-statement: fill in the blockquote below, or delete it if you do not use it. -->

> In the context of {{X}}, facing {{Y}}, we decided for {{Z}} and neglected {{W}}, to achieve {{V}},
> accepting that {{U}}.

## Context

<!--
  The forces at play: the situation, constraints and pressures. Neutral in tone. Do not argue for the
  answer. Link the related ADR when this one splits from, or replaces, another.
-->

{{Context}}

## Considered options

<!--
  Each option the team really weighed, including the one chosen, with pros and cons. Do not add an
  option to make the choice look better.
-->

### {{Option 1}}

- Good: {{pro}}
- Bad: {{con}}

### {{Option 2}}

- Good: {{pro}}
- Bad: {{con}}

## Decision

<!-- Full sentences that begin "We will ...". -->

We will {{the choice}}.

## Consequences

<!-- What follows, good and bad. A list of only good consequences is an advertisement. -->

- {{Consequence}}
