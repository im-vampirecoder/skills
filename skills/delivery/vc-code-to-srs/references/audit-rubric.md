# Audit rubric

Load this for step 5. The audit reads a staged draft cold, against the
code, as if someone else wrote it. It is run by the `vc-srs-auditor`
subagent when the environment supports subagents, otherwise by a
separate pass in the same session that starts from this file and the
draft only, not from the drafting notes.

## Input

The draft folder (`<feature folder>/as-built/.draft/`), the submodule
paths it cites, `labels-and-framing.md`, and the feature's manifest
entry. Nothing else: no drafting reasoning.

## Method

1. Split every pack file into atomic claims: one table row, one use-case
   step, one diagram node or message.
2. For each claim, open the cited lines and decide:
   - **backed**: the line states it → keep;
   - **partly backed**: the line supports part of it → narrow the claim
     to what is backed, or downgrade;
   - **unbacked**: nothing cited supports it → downgrade to 🟡 with an
     open question, or remove it when it adds nothing;
   - **wrong citation**: the claim is true but cites the wrong line →
     fix the citation.
3. Apply the label rules:
   - Intent, purpose, actor identity, priority at ✅ or 🔵 → 🟡 + OQ.
   - ✅ citing a skipped, ignored or `todo` test → 🟡 + Gap.
   - ✅ error whose wording is a key, not quoted catalog text → 🟡 +
     Gap + OQ.
   - 🔵 with fewer than two independent sources → 🟡, or ✅ if one line
     states it outright.
   - A claim about a suspected dead or flagged-off path written as a live
     capability → 🟡 + OQ + the negative search in Gaps.
   - A rule with one line of code and no test stays ✅; add "no test
     covers this" in Gaps only when the rule is risky (money, access,
     data loss).
4. Check the wording: code names outside citations and `evidence.md`,
   invented values, steps a diagram draws that the code doesn't have,
   screens inferred from request fields.
5. Check cross-repo hops: both sides cited, and the client path really
   matches the server route.

## Limits

- Never split, merge or rename the feature, and never change its slug;
  that was settled in the manifest.
- Never compare against other features; judge this pack against its
  code only.
- One audit round. Findings the main session can't apply become Gaps.

## Output

Return, never edit:

```markdown
## Audit: <feature-slug>

**Verdict:** pass | pass with changes | fail

| # | File:line | Claim | Finding | Change |
|---|---|---|---|---|
| 1 | spec.md:42 | Shop staff mark orders shipped | intent at ✅ | → 🟡 + OQ "who ships?" |

**Label counts after changes:** ✅ n · 🔵 n · 🟡 n
**New open questions:** ...
**New gaps:** ...
```

`fail` means more than a third of the claims needed a change, or a
citation pattern is systematically wrong; the main session redrafts once
before going on.
