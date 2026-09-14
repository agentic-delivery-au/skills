---
name: writing-prds
description: Writes and revises product requirements documents that define the problem, the people who have it, and what success looks like, without proposing a solution. Use when writing or revising a PRD, capturing requirements from a brief, notes, a transcript or an interview, or when a document is drifting from stating a problem into designing an answer.
---

# Writing PRDs

The template is [`references/PRD-template.md`](references/PRD-template.md). Read it before you
start. This file governs how to fill it in.

## The one rule

**A PRD states the problem. It never states the solution.**

Who the users are, what they are trying to accomplish, what gets in the way, what solved looks like,
what is out of scope. Nothing about how it gets built.

This is not a style preference. The solution is a separate document, so that the same needs can be
met several ways without rewriting the PRD. A PRD that names a solution has quietly decided the
thing it was supposed to leave open.

The failure is easy to miss, because a solution can be written as though it were a need:

| Solution in disguise                       | The need underneath                                                         |
| ------------------------------------------ | --------------------------------------------------------------------------- |
| Add a rejection-reason column to the queue | A handler must learn why a claim was rejected without leaving the queue     |
| Send a nightly digest email                | A manager must find out about overnight failures before their first meeting |
| Build a bulk-edit screen                   | An operator must correct a hundred records without doing it a hundred times |

If a need can only be phrased as a thing to build, you have not found the need yet. Ask what result
that thing would produce, and write that instead.

## Workflow

Copy this and track it:

```text
PRD progress:
- [ ] 1. Get all of the source, comments and all
- [ ] 2. Interview for what the source does not cover
- [ ] 3. Separate what is true now from what someone wants
- [ ] 4. Draft: problem, users, outcomes, goals, non-goals, metrics
- [ ] 5. Drop the sections that do not apply
- [ ] 6. Check the draft against the rules, fix, repeat
- [ ] 7. Hand over with every open question owned and dated
```

Steps 1 to 3 carry most of the value and most of the mistakes. Do not start drafting because you
have enough to fill the headings. The sections below are the detail behind each step.

## Outcomes

Every outcome carries a priority: Must, Should or Later. Must means the problem is not solved
without it. Push back if the author marks them all Must. That is a list, not a priority, and it
leaves a design team unable to tell what is safe to defer.

Past about eight outcomes, group them under sub-headings and name the group that is the first
release. A real brief will happily produce fourteen, and presenting them flat gives a reader nothing
to hold on to.

Measures belong to outcomes. If a measure appears in both the outcomes table and Success metrics,
delete it from Success metrics. That section carries the aggregate signal, the baselines, and the
date you will measure, not a second copy of the table.

Never invent a baseline or a current-state number. Write "unknown, see Qn", raise the question with
an owner and a needed-by, and move on. A PRD that surfaces what nobody has established is doing its
job. One that guesses is a liability, because a made-up figure reads as evidence and gets quoted
back. Equally, do not manufacture uncertainty. On a small PRD most of this is genuinely known.

## Worked examples

A few sentences in the users' own voice, to stop the outcomes table reading as a wall of
abstractions. They illustrate; they never enumerate. They are written, not transcribed, which is why
the section is not called quotes. Where you do have a real quote, attribute it and link the
transcript under References. Three or four, chosen to bring the most abstract outcomes to life, each
saying which outcome it serves. Drop the section entirely when the outcomes are already vivid, which
is usually the case on a small PRD.

Use the situation-and-motivation shape, *When ‹situation›, I want to ‹motivation›, so I can
‹outcome›*, because it leaves no room to name a solution. Write them as plain paragraphs, not
blockquotes: CommonMark merges consecutive blockquotes separated by blank lines into a single quote
block, and the quote styling implies transcription. Never use the *As a ‹role›, I want ‹feature›*
form: that names a solution, and it belongs in the user stories document, not here.

## Quality attributes are not a third list

There is no non-functional requirements section, and adding one is a mistake. A quality attribute is
either something that must become true for these people, which is an outcome carrying a measure, or
something whatever gets built has to live within, which is a constraint. A separate list duplicates
one of those and then drifts from it, the same way Success metrics drifts from the outcomes table.

"An assessment can be retrieved in minutes" is an outcome. "Records are kept for seven years" is a
constraint. "The service is available" is neither until someone says what depends on it being up.

The cost of having no heading is that nobody remembers to ask. Retention, data residency, security
classification, accessibility, language and expected volume go unmentioned in most briefs, and their
absence is worth recording as an open question rather than passing over. Where volume is known and
small, say so: it rules out more design than it sounds like.

## Sections that overlap

Goals, Non-goals and Success metrics are three separate sections doing three jobs. Goals are
organisational intent at a higher altitude than the outcomes. Non-goals draw the boundary. Success
metrics say how you will know overall. Do not merge them.

## Get all of the source, not the obvious part

Some of what you were given is easy to reach and some is not, and the hard part is often the more
valuable one. What was challenged, corrected or left hanging says more than what was drafted.

If the source is a person, the unasked question is the gap. If it is a conversation, what was
settled at the end may contradict the middle.

If it has a document surface of any kind, a text file, a word processor document, a shared doc, a
design board, a wiki page, the argument about it usually sits beside the body rather than in it:
comments, suggestions, tracked changes, replies, annotations. That is frequently the most useful
part of the whole thing, and it is the first casualty when a tool extracts "the text". Check what
you hold against the original rather than against a conversion of it, and read the resolved state as
well as the content.

An unresolved comment, or a question nobody answered, is an open question with an owner already
attached. Treat it as one.

## Separate what is from what someone wants

People describe what they wish were true in the same breath as what is true, and rarely mark the
change. In conversation it is a slipped tense: "the assessment goes to the approver" can mean it
does, or that it should. In a written brief it can be a whole section. Either way the wished-for
version is often the bulk of what you are given, because it is what the person has been thinking
about.

Only what is true now belongs in the problem. The rest is a solution someone has already started
designing, however early.

So for every sentence you write about the current state, know who said it happens now. Ask: does
this happen at the moment, and if so, who does it? Where nobody has answered, that is an open
question, not a current-state claim.

This is the easiest way for a solution to reach a PRD, and it slips past the rule below, because you
invented nothing. You reported a wish as a fact.

## Claim only what the source says

Every statement of current state has to trace back to the source or to someone who told you. The
ways of exceeding it are quiet, and all of them read as fact afterwards:

- **Added detail.** "that effort hasn't been rolled out to others" says nothing about who uses it
  now. Writing "never rolled out beyond the people who wrote it" invents a fact about current usage.
- **Hedge dropped.** "very likely a delegate would be nominated" is not "a delegate is nominated".
  "To be determined next phase, but broadly X" is not "X". Keep the hedge and point at the open
  question.
- **Causation added.** Where the source lists two observations, do not join them with "so" or "low
  enough that". It may be the reason. It may be a second symptom.
- **Scope widened.** Evidence that safety cannot stand alone is not evidence that neither can.
- **Strength raised.** "Not rolled out to others" is weaker than "not adopted". Use the weaker word.
- **Targets invented.** Do not write a number nobody agreed, including an obvious-looking one.

Tabulating hardens. Summarising into a table, a decisions list or a resolved question is where a
hedge is most likely to disappear, because a cell has no room for "very likely" or "to be
determined". If the hedge will not fit, the claim does not belong in the table.

Where the source stops short of what the document needs, that is an open question, not permission to
fill the gap. Write what is known, name what is missing, give it an owner.

This matters more in a PRD than in most documents, because it is read as the settled account of the
problem and then quoted back in design reviews and sign-offs. A sentence with one invented clause in
it will be believed in full.

## Name the actor

A sentence that describes a group by what they would do, instead of by who they are, says less than
the source did and reads as padding.

> The people whose lens would catch a whole class of risk, particularly content and comms, are
> engaged at the end rather than the beginning.

Who? The source said "the content/comms team". The abstraction is longer, vaguer, introduces the
same people twice, and turns a flat statement into a hypothetical. Write:

> Content and comms are brought in at the end rather than the beginning.

Two tests for any sentence about the current state:

- **Could it appear in a PRD for a different organisation?** If yes, it is not about this one. "The
  people whose lens would catch a whole class of risk" fits every company there is.
- **Can you point at the actor?** A named team, a role on an org chart, a system. Where the subject
  is "the people who", "stakeholders", "those responsible", "the relevant parties" or "key
  personnel", put the name back.

Never go up a level of generality from your source. If the brief names a team, name the team. The
same applies to outcomes: "experts whose lens a risk depends on" is "the right subject matter
experts".

## Interview before writing

Do not fill the template in from a one-line brief. Ask, one question at a time:

- What is going wrong today, and for whom?
- How do you know? What evidence is there: volumes, interviews, incidents, or just a request?
- What do they do instead right now, and what does that cost them?
- What would have to become true for this to be solved? How would you know it had been?
- What is deliberately not in scope?
- What has to be true for this to work at all, that might not be?
- Who has to agree before anyone acts on this?

Stop asking when you have enough for the sections that apply, not when you have covered every
question above.

## Drop sections that do not apply

Every section in the template carries a "drop this if" note. Honour them. A two-week feature for an
audience the team already understands does not need a segments section, a journey link, or a
dependency table. Padding a small PRD with product-launch scaffolding makes it less likely to be
read, not more thorough.

When you drop something a reader might expect, say so in one line rather than deleting silently, so
they know it was considered.

## Detail lives in linked documents

The PRD holds the outcome level. Enumerated detail moves out once it grows:

- Segments with real depth, distinct contexts, a journey worth mapping. Summarise here, and link a
  user journeys document.
- A story list running past about a page. Move it, link it, keep the outcomes here, and keep three
  or four in the PRD under "Worked examples".
- Meeting notes, interviews, workshop output, research, analytics. State the finding under Evidence,
  and put the source under References.

Never reproduce a linked document's content in the PRD. Link it and move on.

Annotate every link under References with what is in it and why someone would open it. A bare list
of URLs is not a reference section. Link only what you have read and what backs a claim the document
actually makes, and never let a link smuggle a solution in: pointing at a design document is fine,
summarising its approach is not.

## Revising an existing PRD

**Fold answers in, then delete the question.** When an open question is answered, update the section
it affects and remove the row. The body is the source of truth. An answer that lives only in the
open-questions table is lost, and a log that keeps every resolved question next to the open ones
stops being usable at the point it matters most, when there are forty of them. Whatever holds this
document's history already records that the question was asked.

**Watch sign-off, but only for substantial change.** A change invalidates a sign-off when someone
who signed the previous version would want to know about it before the work went ahead. Adding or
removing a Must outcome. Changing what the problem is. Moving something into or out of Non-goals.
Changing who has to agree.

Almost nothing else qualifies. Clarified wording, a typo, a new reference, a tightened measure, or
an answered question that confirms what the document already said: none of these need a fresh
signature, and treating them as though they do teaches people to sign without reading.

Where it does invalidate: bump the version, clear the sign-off table, say so in the status block.
Where you are unsure, say which you think it is and let the author decide.

Every revision updates the status block: version, date, and one line on what changed. Do not add a
revision history table, because wherever the document lives already keeps one and a hand-maintained
copy goes stale.

## Cross-references are links

Outcomes, risks and open questions are numbered so other parts of the document can point at them,
which only helps if pointing at them takes the reader there. Put an anchor on each id cell and write
every mention as a link:

```markdown
| <span id="q3"></span>Q3 | How is the lead chosen? | Kara Collins | Before workflow design |

...the selection logic is unsettled. See [Q3](#q3).
```

Use `<span>`, not `<a>`. It matters more than it looks. Converting to a Word document with pandoc,
`<a id>` and `<a name>` produce the link but no bookmark for it to land on, so every cross-reference
arrives dead. `<span id>` produces the bookmark. Both survive rendering on a git host, and where the
HTML is stripped entirely the cell still reads Q3 and the reference still reads Q3, so nothing is
lost either way.

Pandoc's own `[Q3]{#q3}` span syntax also produces the bookmark, but renders as literal text on a
git host, so it is the wrong trade.

Deleting an answered question breaks whatever pointed at it. Fix the references in the same edit. A
link checker will catch what you miss, and is worth running for that reason alone.

## Check the draft before handing it over

Read what you wrote against this list. Every item has caught a real error in a finished draft.

- **No solution.** Find anything naming a thing to build and restate it as the outcome it would
  produce.
- **Every current-state sentence has someone behind it.** For each, name who said it happens today.
  Where nobody did, it becomes an open question.
- **Hedges survived.** Take anything written as settled, agreed or decided back to the words in the
  source. Check tables first, since that is where hedges go missing.
- **No invented numbers.** Every figure traces to a source or says it is unknown.
- **Actors are named.** No "the people who", "stakeholders" or "those responsible".
- **Every open question has an owner and a needed-by.**
- **Every cross-reference resolves.** Deleting an answered question leaves anything pointing at it
  dangling.
- **Acronyms expanded on first use, and every link resolves.**

Fix what the pass turns up, then run it again. Stop when a pass finds nothing. A draft that has
never been read against these rules is not finished, however complete it looks.

## Language

Plain English. No codenames, no internal jargon, nothing a new stakeholder would have to ask about.
Concrete over vague: "about 11 minutes each, roughly 40 times a week" beats "inefficient". Short
sentences. If a paragraph is doing two jobs, split it.

Acronyms get their full term the first time they appear, with the acronym in brackets after, and the
term linked to whoever is authoritative for it. The body responsible beats an encyclopedia entry:
the [World Health Organization](https://www.who.int/) (WHO), not a summary of WHO. Write it in that
order rather than acronym-first, which reads badly in a summary where several land together. After
the first use, the short form is fine.

Skip the gloss for acronyms that have stopped being acronyms for this audience: ATM, PDF, CEO, USB,
and in a technical document API or CPU. The test is this document's readers rather than a universal
list, so API needs no gloss for an engineering team and does need one in a board paper. Check the
link resolves before you include it. A PRD often goes to someone outside the team who will not ask
what a funder's initials mean, so the gloss is for them.

Never invent an expansion. Where you cannot source what an acronym stands for, leave it and raise it
as an open question naming who can say. A plausible guess reads as fact and is worse than the gap.
