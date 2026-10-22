---
name: prototype-before-ask
description: >
  Use when you are about to ask the person or the lead a "which approach", "how should this behave" or "which is
  faster" question, and the answer is a fact you could observe by running something: behaviour, timing, output,
  whether a check separates two cases. Settle it with a throwaway script and report the decision with its evidence.
  Reserve the question for a product or preference call no experiment can settle, and for anything visual.
---

# Prototype before you ask

A "which approach" fork is a question only when nobody can observe the answer. Before you ask one, classify it:

- **Observable by running something** (which call is faster, whether the parser accepts the input, what the API
  returns, whether a timeout fires, whether a test separates the two behaviours): not the person's to answer.
  Settle it here and report the decision.
- **A product or preference call** (what a user should see, what the feature is for, which of two correct
  behaviours they want): ask, in one line, the way your role says.
- **Visual** (layout, density, how something looks or feels): ask. This rig has no rendering surface to compare
  variants on, so a visual fork is never decided silently.

If the answer is already in the code, the docs or the history, read it and cite it. A sketch is for what reading
can't tell you.

## The round

You own the decision, not the code. The prototype is a throwaway instrument; the real change follows your role.
Speed over polish: no planning, no abstractions, no tests, and code quality doesn't matter.

1. **Name the decision** in one sentence, with the variants. No decision means no prototype: carry on with your
   role.
2. **Build the smallest script that exercises the question**, in a scratch folder at the root of the clone,
   `.scratch/<decision-slug>/`. Never in your worktree and never in the repository's source tree. The first time,
   add one line, `/.scratch/`, to `.git/info/exclude`, the same way the rig keeps OpenRig's own files out of commits.
   Reuse the repository's installed dependencies; import from its source if that is the cheapest way to exercise the
   question.
3. **Run the variants side by side, labelled.** Two or three competing versions, each with a name, run under the
   same input in the same session. For a timing decision, run each variant more than once and keep the spread, not
   one number; say which machine and runtime it ran on.
4. **Observe, don't assert.** Print the output, log the timing, and read it. The observation is the test here;
   there is nothing to assert against. If the result is a wash, say so: a wash is a finding, and the tie-break is the
   smaller change.
5. **Decide and move on.** Write the result down as a short table (variant, what it showed, cost) with a
   recommendation and the scratch path, then act on it. Say plainly that the prototype is throwaway.

Keep the round small: minutes, not an afternoon. If it grows past a few scripts, the fork wasn't observable the way
you thought, or it is a real design decision. Stop and ask.

## No hand-off for the round itself

Whichever seat holds the thread when the fork appears resolves it, in that seat, before carrying on. The round
never goes to another seat as a queue item.

- **Lead, during scoping:** the decision and its evidence go into the brief you are already writing, under what
  already exists or open questions (now closed), so the builder inherits a settled call and the path to re-run it.
- **Builder, mid-implementation:** the decision and its evidence go into your report to the code reviewer and the
  QA seat, with the commit it shaped and the scratch path, so they can re-run the sketch. Put it in the note to the
  lead too if it changes what a user gets.

Only the outcome crosses seats, inside the queue item you were going to write anyway. If a row carries one, tag it
`--tags kind:prototype-decision` alongside its scope tags, so it can be found later; nothing reads the tag today.

## Report

In the brief or the report, in this order: the decision in one line; the variants, each with what it showed;
the recommendation and why; the scratch path; "throwaway, not shippable." Keep the evidence to what you saw at the
source, the rig's culture: a claim names the command and what you saw.
