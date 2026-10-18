# Flow diagram conventions

Rules for section 1 of `ux/user-flow.md`. `check_user_flow.py` enforces
the ones marked **(checked)**; the rest are for the reviewer.

## Nodes

- **One node per line, one edge per line (checked).** Define every node
  on its own line before using it in an edge. Inline definitions inside
  an edge are not understood by the check.
- **Screens**: `S<n>["[<n>] <Name>"]`, numbered in the order a user first
  meets them on the happy path. Each screen appears once; return visits
  are edges back to the same node.
- **Decisions**: `D<n>{"<question>?"}`, phrased as the question the system
  or user answers ("Card accepted?"), never as an action.
- **States that aren't screens** (a toast, an inline error) belong to the
  screen they appear on; they are listed in mockups, not drawn here. Draw
  a separate node only when the user lands somewhere new.

## Classes

| Class | Meaning | How |
|---|---|---|
| `happy` | on the main success path | `:::happy` on the node line |
| `error` | something failed; shows an `ERR-` | `:::error` |
| `edge` | allowed but unusual: limits, timeouts, interrupted flows, empty data | `:::edge` |
| `entry` | where a user can start (checked: everything must be reachable from an entry) | `class S1,S7 entry` |
| `terminal` | the flow legitimately ends here (checked: other nodes need a way out) | `class S3 terminal` |
| `temporary` | a state that must end: locked, expired, pending (checked: needs an exit to another node) | `class S5 temporary` |

Every screen gets one of `happy`, `error` or `edge`. No `entry` class
means the first node defined is the only entry.

## Branches

- **Every decision has 2+ exits, all labelled (checked).** A screen with
  more than one exit labels all of them (checked).
- **Cover the three cases at each decision**: the happy outcome, each
  failure the PRD's Errors table lists for that step, and the edge cases
  from its State transitions and Interrupted flows tables. A case the
  PRD doesn't cover is a PRD gap, not a new branch with invented rules.
- Label edges from screens with what the user does (`"Pay"`), and edges
  from decisions with the outcome (`"No, limit reached"`).

## Quoting and characters (checked)

| Right | Wrong | Why |
|---|---|---|
| `S5["[5] Locked: try later"]` | `S5[Locked: try later]` | special characters (`: ( ) [ ] # & < > /`) need quotes; always quote |
| `-->\|"No, tries left"\|` | `-->\|No, tries left\|` | quote edge labels too |
| `"Terms & conditions"` | `"Terms &amp; conditions"` | write the character, never an HTML entity |
| `"Card declined<br/>Try another"` | `"Card declined\nTry another"` | `<br/>` for a line break |
| `"Shows the Save button"` | `"Shows the "Save" button"` | no quotes inside a label |

## Size

Keep one diagram per feature. Past about 25 nodes, group each flow in a
`subgraph <flow-slug>` … `end` block rather than splitting the file.
