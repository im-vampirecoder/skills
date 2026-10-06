---
name: vc-prompt-enhancer
description: Expand a quick, rough prompt into a detailed, codebase-grounded one - adds file references, conventions, and a concrete step breakdown - before you send it as a real request. Ported from Augment Code's Ctrl+P Prompt Enhancer.
disable-model-invocation: true
---
# Prompt Enhancer

Takes a quick, rough prompt and expands it into a detailed, codebase-grounded  
one before it becomes a real request. You will execute the  
scouting yourself with local tools (Glob/Grep/Read, or the `scout` skill for
heavier search).

## Process

1. **Capture the raw input.** Use the skill argument if given, otherwise the
 rough prompt in the user's immediately preceding message.
2. **Gauge groundedness.** If the input is too short or vague to ground in
 anything real (a single vague word, no discoverable subject), ask ONE
 clarifying question instead of inventing detail. Don't fabricate specifics
 the codebase doesn't support.
3. **Scout for context.** Search the codebase for what the prompt implies:
 relevant file paths, existing naming/style conventions, similar past
 implementations or patterns to mirror. Ground everything in what's
 actually there.
4. **Compose the enhanced prompt:**
   - One line stating the concrete goal.
   - Specific file/path references found while scouting.
   - A short numbered breakdown of concrete steps or checks, grounded in the
   repo - not generic boilerplate.
   - Domain/convention language the codebase already uses.
   - Keep it a real task brief, not a wall of text - 4-8 lines typical.
5. **Present, don't execute.** Output the enhanced prompt in a fenced code
 block, ready to copy or reuse as the next request. Do not start
 implementing the task - the enhanced prompt is the deliverable.
6. **Offer iteration.** Ask whether to run it as-is, edit it, or re-enhance
 with different emphasis.

## When enhancement isn't possible

- Still too short/unclear after one clarifying question: say so plainly
instead of guessing.
- No matching context found in the codebase: say so, and hand back a
cleaned-up (not fabricated) version of the original prompt.

