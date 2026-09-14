<!--
  PRD TEMPLATE

  A PRD defines the problem, not the solution.

  It says who the users are, what they are trying to accomplish, what gets in
  their way, what "solved" looks like, and what is explicitly out of scope. It
  stops there. No proposed approach, no feature list, no architecture. The
  solution is a separate document, because the same needs can be met several
  ways and the PRD should survive changing your mind about which.

  HOW TO USE THIS
  - Replace every {{placeholder}}, including the surrounding braces.
  - Delete each guidance comment as you go, including this one. Those comments
    carry the rules, not just advice: when a sign-off expires, what to do with
    an answered question, when a section may go. Deleting them does not delete
    the rules, and the finished PRD will not carry them. Before revising a PRD
    months later, open the blank template again, or the writing-prds skill if
    you have it.
  - Delete whole sections that do not apply. Every section carries a "Drop this
    if" note. Deleting is expected rather than a shortcut. A two-week feature
    for an audience you already understand does not need product-launch
    scaffolding.
  - You might not have everything, and where you do not, that is not a failure.
    Part of what a PRD does is force the unknowns into the open. Write what you
    know, mark what you do not, and give every unknown an owner in Open
    questions. A document with honest gaps and names against them is worth more
    than one that reads complete because somebody guessed. On a small PRD most
    of this will already be known, so do not manufacture uncertainty either.
  - Claim only what your source says. Do not add detail it does not carry, do
    not drop a hedge it does carry, and do not join two observations with "so"
    unless it did. "Not rolled out to others" is weaker than "not adopted", and
    the weaker word is the right one. Where the source stops short of what a
    section needs, that is an open question with an owner, not permission to
    fill the gap.
  - Name the actor. Where a sentence describes a group by what they would do
    instead of who they are, put the name back: "the people whose lens would
    catch a whole class of risk" is "content and comms". A sentence that would
    fit any organisation is not about this one.
  - Keep it in plain language. No codenames, no internal jargon, nothing a new
    stakeholder would have to ask about.
  - Give an acronym its full term the first time it appears, with the acronym
    in brackets after it, and link the term to whoever is responsible for it
    rather than to an encyclopedia entry.
    Skip that for acronyms that have stopped being acronyms for this audience,
    such as ATM, PDF or CEO. Never invent an
    expansion: where you cannot source one, leave the acronym alone and raise
    it as an open question.
-->

# {{Product or feature name}}

|               |                                                    |
| ------------- | -------------------------------------------------- |
| Version       | {{0.1}}                                            |
| Status        | {{Draft \| In review \| Signed off \| Superseded}} |
| Date          | {{YYYY-MM-DD}}                                     |
| Owner         | {{name}}                                           |
| This revision | {{one line on what changed}}                       |

<!--
  Status: Draft = still being written. In review = stakeholders are reading it.
  Signed off = agreed, and the sign-off below names the version they agreed to.
  Superseded = a newer PRD replaces this one; link it.

  Drop this if: never. Sign-off is meaningless without a version to attach it to.
-->

## Summary

{{Two or three sentences. What problem, for whom, and why it is worth solving now. Someone should be
able to read only this and know whether the rest of the document is relevant to them.}}

<!-- Drop this if: never. -->

## Problem

{{What is going wrong today. Who it affects. What it costs them in time, money, errors and abandoned
work. Be concrete: "handlers re-run the report by hand, about 11 minutes each, roughly 40 times a
week" beats "the process is inefficient".}}

### Evidence

{{How you know this is real. Support volumes, interview counts, analytics, churn reasons, a specific
incident. If the only evidence is that someone asked for it, say so. It is still evidence, just
weaker, and naming it honestly lets a reader weigh it.}}

<!--
  Write only what is true now. Whoever briefed you will describe what they
  wish were true in the same breath, and rarely mark the change: in speech it
  is a slipped tense, in writing it can be a whole section. The wished-for
  version is often the bulk of it, because that is what they have been
  thinking about, and none of it belongs here.

  For each sentence, know who said it happens today. Where nobody has said so,
  that is an open question, not a fact about the present.
-->

<!--
  State the evidence here in a line or two and link the source under References,
  so a reader who wants the full interview notes can get to them without this
  section swelling.

  Drop this if: never. If you cannot state the problem, you are not ready to
  write the rest.
-->

## Who it's for

{{The people with this problem. Name the segments and roughly how many, or how much of the business
they represent. A sentence or two each.}}

<!--
  Drop this if: this extends an existing product to an audience that has not
  changed and is already documented elsewhere. Link that document instead of
  restating it.

  If the audience has real depth (several segments, distinct contexts, a journey
  worth mapping) keep a short summary here and link a user journeys document
  rather than growing this section.
-->

## Needs and outcomes

<!--
  The heart of the document. State what must become true for these people, and
  how you would know it had. Resist naming a feature: if a need can only be
  phrased as a thing to build, restate it as the result that thing would
  produce.

  "A handler must learn why a claim was rejected without leaving the queue" is
  a need. "Add a rejection-reason column" is a solution written as though it
  were a need.

  Priority is Must, Should or Later. Must means the problem is not solved
  without it. If everything is Must, you have not prioritised. A reader should
  be able to tell what is lost if the Laters never happen.

  Past about eight outcomes, group them under sub-headings and say which group
  is the first release. A flat list of fourteen gives a reader nothing to hold
  on to.

  Where there is no baseline, write "unknown, see Qn" and raise the question
  with an owner. Never estimate one to fill the cell: a made-up number reads as
  evidence, gets quoted back, and cannot be traced. The gap is useful output,
  because it tells a stakeholder what to go and measure.
-->

### Outcomes

{{What must become true, each with something observable that would tell you it had. Number them so
other documents can refer to them.}}

| ID                      | Outcome               | Priority                    | Measured by           |
| ----------------------- | --------------------- | --------------------------- | --------------------- |
| <span id="o1"></span>O1 | {{what becomes true}} | {{Must \| Should \| Later}} | {{observable signal}} |
| <span id="o2"></span>O2 | {{what becomes true}} | {{Must \| Should \| Later}} | {{observable signal}} |

### Worked examples

<!--
  A few sentences in the users' own voice, to make abstract outcomes land. An
  outcomes table becomes abstract quickly, and this is where a reader feels who
  the document is about.

  These are written to illustrate. They are not transcribed from an interview,
  which is why the section is not called quotes. Where you do have a real quote,
  attribute it to the person and link the transcript under References.

  This shape works well, because describing a situation and a motivation leaves
  no room to name a solution:

    When ‹situation›, I want to ‹motivation›, so I can ‹expected outcome›.

  Worked example:

    **A claims handler**, on O1: when a claim is rejected overnight, I want to
    know the reason before the client calls, so I can answer without stalling
    them.

  Do not use blockquotes. Several in a row separated by blank lines are merged
  into one quote block by CommonMark, so they render as a single quotation, and
  the quote styling implies these were transcribed when they were written.

  Deliberately not the "As a ‹role›, I want ‹feature›" form. That shape names a
  solution, which is the one thing this document does not do.

  These illustrate, they do not enumerate. Three or four is right, chosen to
  bring the most abstract outcomes to life. Say which outcome each one serves.

  Drop this if: the outcomes above are already vivid enough to picture, which is
  usually the case on a small PRD.

  Where there are dozens, still keep three or four here, move the full set to a
  user stories document, link it below, and keep the outcomes in this document
  either way.
-->

**{{who they are}}**, on {{O1}}: {{when ‹situation›, I want to ‹motivation›, so I can ‹expected
outcome›}}.

{{Where there are more than a handful, link the user stories document here.}}

## Goals

{{What the organisation is trying to achieve by solving this. Not what becomes true for the users,
which is the outcomes table above, but why it is worth doing at all: the exposure it reduces, the
cost it removes, the commitment it meets. Two or three, in plain terms.}}

<!-- Drop this if: never. -->

## Non-goals

{{What this deliberately does not address, and briefly why. Be generous here, because this is what
stops scope creeping later: the adjacent problems everyone will bring up, the tempting extensions,
the things a reader might otherwise assume are included.}}

<!--
  Drop this if: never. An empty non-goals section is a warning sign that the
  boundary has not been thought about.
-->

## Success metrics

{{How you will know overall, and when you will look. Give a baseline and a target where you have
one. "Time-to-reason from 11 min to under 2 min" is checkable. "Improve efficiency" is not.}}

<!--
  Do not restate the per-outcome measures here. Those belong in the Measured by
  column of the outcomes table, and repeating them guarantees the two drift
  apart the first time either is edited. This section carries what that table
  cannot: the aggregate signal a sceptic would accept, the baselines you have or
  still need to capture, and the date you will measure.

  Where you have no baseline, name the gap and who will close it rather than
  estimating one to fill the space.

  Drop this if: never, but keep it to a few lines. If it is longer than the
  outcomes table, it is duplicating it.
-->

## Context and constraints

{{What the solution will have to live within, without saying what it is. Existing systems and data,
regulatory or contractual obligations, budget or appetite, deadlines that are real rather than
aspirational, platforms that must be supported.}}

{{Quality attributes belong here too, and are easy to forget because there is no heading calling for
them: how long records must be kept, where data may live, what classification it carries, who must
be able to use it, which languages, and the volume it has to cope with. Say when one has been
established and when nobody has raised it.}}

### Appetite

{{How much this problem is worth solving. "Two weeks" or "one quarter", rather than an estimate of a
solution you have not chosen yet. This is a constraint on whoever designs it, not a prediction.}}

<!--
  There is deliberately no non-functional requirements section. A quality
  attribute is one of two things already covered: something that must become
  true for the people in this document, which is an outcome with a measure, or
  something whatever gets built has to live within, which is a constraint here.
  A third list duplicates one of them and then drifts from it.

  "Retrieval takes minutes" is an outcome, measured. "Records are kept seven
  years" is a constraint. Neither needs a heading of its own.

  Drop this if: there are no constraints beyond the obvious.
-->

## Assumptions and risks

{{What you are taking on faith that could turn out to be wrong, and what would derail this. For each
one, say what you would do about it: test it early, accept it, or mitigate it. Record a response for
every risk.}}

| ID                      | Assumption or risk  | If it's wrong    | Response                   |
| ----------------------- | ------------------- | ---------------- | -------------------------- |
| <span id="r1"></span>R1 | {{what we believe}} | {{what happens}} | {{test, accept, mitigate}} |

<!--
  Drop this if: this is a small extension resting on no new assumptions. Say
  that in one line rather than deleting silently, so a reader knows it was
  considered.
-->

## Dependencies

{{Other teams, systems, vendors, approvals or prerequisites this waits on. Name who owns each and
whether they know.}}

<!-- Drop this if: this is self-contained. -->

## References

<!--
  Where a reader goes to check your working. Meeting and interview notes,
  workshop output, research, analytics, support queries, prior art, related or
  superseded PRDs, and the design document once it exists.

  Annotate every link. A bare list of URLs is not a reference section. Say what
  is in each one and why someone would open it, so a reader can decide without
  clicking. Link only things you have actually read and that back something
  claimed above.

  This section holds sources. It does not hold solutions: linking a design
  document is fine, summarising its approach here is not.
-->

- [{{Discovery workshop notes, 12 March}}](https://example.com/notes). {{Where the 40-times-a-week
  figure in Problem comes from, plus the full transcript and the six handler interviews.}}
- [{{title}}](https://example.com/doc). {{What is in it, and why a reader would open it.}}

<!--
  Drop this if: there is nothing to link. Do not invent references to fill it.
-->

## Open questions

<!--
  A live log. Questions get raised, answered, and folded back into the document
  above.

  When a question is answered, do two things: update the section it affects,
  and delete the row. The body of the document is where the answer lives. An
  answer that lives only in this table is lost, and a table that keeps every
  resolved question alongside the open ones is unusable by the time there are
  forty of them. Whatever holds this document's history already records that the
  question was asked.

  Needed by is the point the answer must exist: "before design sign-off",
  "before v1.0", or a date. A question with no needed-by never gets chased.

  Cross-references are links. Each id cell carries an anchor, so a mention
  elsewhere is written [Q3](#q3) rather than bare, and a reader jumps to the row
  instead of scrolling for it. The same goes for outcomes and risks. Where the
  anchor is stripped, by a paste into a document tool for instance, the cell
  still reads Q3 and the reference still reads Q3, so nothing is lost.

  Deleting an answered question breaks anything pointing at it. Fix the
  references in the same edit.
-->

| ID                      | Question     | Owner    | Needed by                  |
| ----------------------- | ------------ | -------- | -------------------------- |
| <span id="q1"></span>Q1 | {{question}} | {{name}} | {{before design sign-off}} |
| <span id="q2"></span>Q2 | {{question}} | {{name}} | {{YYYY-MM-DD}}             |

<!--
  Drop this if: never. An empty log says the document has been read and nothing
  is outstanding, which is worth saying.
-->

## Sign-off

{{Who has to agree before this is acted on, and what they agreed to. Record the version, because a
signature against version 0.3 says nothing about version 0.7.}}

| Name     | Role     | Version signed | Date           |
| -------- | -------- | -------------- | -------------- |
| {{name}} | {{role}} | {{0.3}}        | {{YYYY-MM-DD}} |

<!--
  A material change to Problem, Needs and outcomes, or Non-goals after sign-off
  invalidates it: bump the version, clear this table, and say so in the status
  block at the top. Wording and typo fixes do not.

  Drop this if: this is internal and nobody outside the team needs to agree.
-->

<!--
  There is deliberately no revision history section. Wherever this document
  lives (git, Google Docs, Notion) already keeps one, and a hand-maintained
  table goes stale. The status block at the top carries the version, the date,
  and one line on what changed in this revision, which is what a reader needs
  before they start. Add a history table only if this will live somewhere that
  tracks nothing.
-->
