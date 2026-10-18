# Labels and wording

Load this for drafting and for the audit. Two rules carry the pack: the
confidence label says how much the code really proves, and the prose is
in business words.

## The three labels

| Label | Use when | Source cell |
|---|---|---|
| ✅ | The code states it at the cited line: a validator, constant, guard, enum value, migration column, route, exact message, or an **active** test asserting the behaviour | At least one citation, pointing at the line that states it |
| 🔵 | You inferred it, and two or more **independent** places in the code back the inference (two services apply the same rule; an enum value plus a method that sets it) | Two or more citations |
| 🟡 | The code doesn't say: why a rule exists, who the real actor is, the business goal, priority, anything a skipped test or a flagged-off path suggests | A citation if one hints at it, else `-`, plus an open question |

Code is strong on *how* and silent on *why, for whom, what for*. Reading
the code never upgrades intent to ✅.

## Right and wrong

| Wrong | Right | Why |
|---|---|---|
| "Accounts lock after 10 failed sign-ins to stop brute-force attacks." ✅ | "Accounts lock after 10 failed sign-ins." ✅ + "The lock exists to stop brute-force attacks." 🟡 + OQ | The number is in the code; the reason isn't |
| "Shop staff ship orders." ✅ citing the `Ship()` method | "An order can move from placed to shipped." ✅ + "Shop staff mark orders as shipped." 🟡 + OQ ("who ships, from where?") | A method doesn't name its caller |
| "Cancelling refunds the customer." ✅ citing a test marked skip | "Cancelling refunds the customer." 🟡 + Gap "tested only by a skipped test" | A skipped test proves nothing |
| Error shown as `orders.not_found` with ✅ | ``key `orders.not_found` (unresolved)`` 🟡 + Gap + OQ | Only quoted catalog text is ✅ |
| "Users can place orders through the legacy endpoint." ✅ | Gap: "legacy order path is marked obsolete; no caller found (`grep ... src/shop-app`)" + OQ | Obsolete or uncalled code isn't a live capability |
| "The system calls `OrdersController.PlaceOrder`, which saves to `dbo.Orders`." | "The system saves the order as placed." ✅ S1:26 | Code names belong only in citations and `evidence.md` |
| "Validates the DTO with `RuleFor(x => x.Items).NotEmpty()`." | "An order must contain at least one item." ✅ S2:9 | Say what it means for the user |
| "P0: placing an order." | (no priority) | Priority is a business decision; leave it to the PRD review |
| "Probably also sends a confirmation email." | (nothing, unless the code sends one) | Never add a step the code doesn't have |

## Business words

- Name actors by role ("signed-in customer", "shop staff"), not by
  claim, policy or table name. Use `docs/glossary.md` terms; replace a
  word its Avoid column lists.
- Keep endpoint, class, function, table, column, SDK and library names
  out of every pack file except citations and `evidence.md`.
- Write real values: "at most 20 items", "between 4 and 10 characters",
  "within 15 minutes", never "a configurable limit" when the value is in
  the code. A value that comes from configuration is "set by
  configuration (`Orders:MaxItems`)" with the key cited, never a guessed
  number.
- Quote user-facing text exactly, keeping its language and punctuation.

## Diagrams

- Draw only steps the code has. An inferred step keeps its label in the
  node text ("Staff ships order 🟡").
- Each flow gets a `sequenceDiagram` (actors, the app, services,
  `alt`/`opt` for failures) and a `flowchart` (steps, decisions, real
  values on nodes).
- Quote every flowchart label: `B{"Cart empty?"}`, `-->|"Yes"|`. No `;`
  or `#` in sequence messages or state transition labels, no HTML
  entities, transition labels under 40 characters (explain in prose).
- `states.md` only for an entity with two or more states in code;
  `erd.md` only when the feature persists data. Otherwise omit the file
  and write `_Omitted: <reason>._` in the spec's matching section.

## Screens

Fill `## Screens` only from real UI code (a page, view, screen or
template). A backend-only feature omits the section; never infer a
screen from request fields.
