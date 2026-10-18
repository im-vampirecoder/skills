# Design Brief and Directions

Loaded by `vc-create-ui-mockup` step 4. Follow-baseline work only
writes the brief (from `DESIGN.md`); greenfield work also explores
directions.

## The brief

A short, fixed statement that every screen is judged against. Write it
into `ux-spec.md` and don't let it drift between screens.

| Line | What it says |
|---|---|
| Context | Who uses the product, on which devices, in what setting, how often |
| Character | Three adjectives the UI should give off, taken from the users and the domain (e.g. "calm, exact, quick" for an ops console) |
| Density | Compact, regular or spacious, and why |
| Color strategy | How much color: mostly neutral with one accent for action and state, or a stronger brand presence — and the accent's job |
| Type | Families and the scale ratio; one family for most product UI |
| Shape and depth | One radius system and one way to show layers (borders, tints, or shadows) |
| Signature | The one detail that makes it recognisably this product, drawn from its domain (a status timeline, a ledger-style table…) |

Every line must trace to something in the PRD, the users, or the
baseline. If it can't, rewrite it.

## Greenfield: 2-3 directions

1. Write 2-3 briefs that differ in a way the user can actually feel —
   e.g. density, color strategy, character — not three shades of the same
   idea. Each is a reasonable answer to the same PRD.
2. For each, build **one** preview of the feature's most important screen
   in `ux/directions/<n>-<short-name>.html`, using a small token set:
   - neutrals: one grey family tinted toward the accent hue, 6-8 steps;
   - one accent (plus hover/pressed), and status colors for success,
     warning, danger, info that differ in lightness, not only hue;
   - type: one or two families, a scale of 5-7 steps;
   - spacing: a 4- or 8-based scale; radius: 2-3 values; one shadow or
     border style for raised surfaces;
   - every text/background pair at 4.5:1 or better (3:1 for large text
     and UI boundaries).
3. Show the briefs side by side with their previews (paths), and ask the
   user to pick one, combine named parts ("2's density with 1's color"),
   or ask for another round.
4. Write the chosen tokens to `docs/design-system/<app>/tokens.json` in
   the list shape described in
   `../vc-extract-design-system/references/claude-design-sync.md`
   ("File shapes"), and the brief as the Foundations section of the
   seeded `DESIGN.md`.

## Avoid the generic look

Whatever the direction, check the previews for the marks of generated,
characterless UI and remove them unless the brief asks for them:

- a purple-to-blue gradient as the default accent; gradient text;
- every card with the same rounded corners, shadow and a colored side bar;
- emoji used as icons or section markers;
- everything centered; a big hero on a product screen that should start
  with the work;
- three equal feature cards as the default layout;
- vague copy ("Unlock", "Seamless", "Supercharge"), placeholder names
  ("John Doe", "Acme"), and invented statistics.
