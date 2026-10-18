# Cross-stack recipes

Load this for every feature, before the stack file (`recipes-dotnet.md`,
`recipes-js-ts.md`, `recipes-mobile.md`). Commands run from the tracking
repo root against one submodule, `R=<submodule_root>/<repo>`. Every
command prints `path:line` (grep `-n`, with `-H` so a single file still
shows its path), and that output is what gets cited, word for word.

## Rules for every recipe

- **Read only.** `cat`, `grep`, `find`, `head`, `sed -n`, `wc`, and
  `git -C "$R" rev-parse HEAD`. Never build, run, install, format, or
  touch git state. Never run the tests.
- **Cite the full repo path** as the command printed it:
  `src/shop-api/Controllers/OrdersController.cs:23`, never
  `OrdersController.cs:23` and never `.../OrdersController.cs`. Two
  submodules often have files with the same name.
- **Skip generated and vendored code:** `node_modules`, `bin`, `obj`,
  `dist`, `build`, `.next`, `Pods`, `DerivedData`, `.dart_tool`, `.gradle`,
  `vendor`, `coverage`, `*.min.*`, `*.g.dart`, `*.Designer.cs`. The helper
  below does it for you.
- **"Not found" is evidence.** When a search comes back empty, record the
  exact pattern and scope you searched in Gaps. "Searched and found
  nothing" and "didn't search" are different findings; only the first
  can support a claim.
- **Secrets.** Read variable names only, from `.env.example`,
  `appsettings.json` keys, `*.xcconfig` keys and the like. Never open
  `.env` or `appsettings.*.local.json` style files, never copy a value
  into the pack, and never print one in the console.
- **Don't pipe `$(find ...)` straight into `grep -r`.** If `find` prints
  nothing, `grep -r` searches the current directory instead. Use
  `find ... -print0 | xargs -0 grep -nH ...`.

```bash
R=src/shop-api   # one submodule at a time
# Every source file, without vendored/generated folders. Reused by the recipes below.
srcfiles() { find "$R" \( -name node_modules -o -name bin -o -name obj -o -name dist -o -name build \
  -o -name .next -o -name Pods -o -name DerivedData -o -name .dart_tool -o -name .gradle -o -name vendor \
  -o -name coverage -o -name .git \) -prune -o -type f ! -name "*.min.*" ! -name "*.Designer.cs" \
  ! -name "*.g.cs" ! -name "*.g.dart" ! -name "*.freezed.dart" "$@" -print0; }
srcfiles | xargs -0 wc -l | tail -1          # size, for the scope gate
```

## T. Tests: expected behaviour, boundaries, edge cases

Tests are the best source for what the code is expected to do: the
boundary (20 items accepted, 21 rejected), the multi-step flow, the rule
that runs backwards (counter resets after a good sign-in). Read them as a
source, not just to count them.

```bash
# Test names and assertions, per framework family (pick what the stack uses)
srcfiles \( -name "*.test.*" -o -name "*.spec.*" \) | xargs -0 grep -nH -E "describe\(|it\(|test\(|expect\(" | head -80
srcfiles -name "*Tests.cs" | xargs -0 grep -nH -E "\[(Fact|Theory|Test|TestMethod|InlineData)|Should|Assert\." | head -80
srcfiles \( -name "*Test.kt" -o -name "*Tests.kt" -o -name "*Test.java" \) | xargs -0 grep -nH -E "@Test|assert|verify\(" | head -80
srcfiles -name "*Tests.swift" | xargs -0 grep -nH -E "func test|XCTAssert|#expect" | head -80
srcfiles -name "*_test.dart" | xargs -0 grep -nH -E "test\(|testWidgets\(|expect\(" | head -80
# Skipped or unfinished tests — never cite these as ✅
srcfiles | xargs -0 grep -nH -E "Skip *=|\.skip\(|\bx(it|describe|test)\(|\.todo\(|@Disabled|@Ignore|\[Ignore|XCTSkip|skip: *true" | head -40
```

- Active test asserting a behaviour → ✅, cite `test-file:line` of the test
  (its name line, or the assertion).
- Skipped, `todo` or ignored test → 🟡 plus a Gap row ("tested only by a
  skipped test"). The checker fails a ✅ that cites a skipped test.
- A test proves the behaviour, never the reason. "Rejects 21 items" is ✅;
  "because one van carries 20" is still 🟡 plus an open question.
- `head -80` is a reading aid. If it truncates, narrow the pattern to the
  feature's files rather than sampling.

## M. Message catalogs: the real wording of errors and labels

Code usually raises a key (`orders.too_many_items`, `R.string.err_limit`,
`l10n.cartEmpty`); the sentence the user sees lives in a catalog.

```bash
# Find the catalogs
srcfiles \( -name "*.resx" -o -name "*.xcstrings" -o -name "Localizable.strings" -o -name "strings.xml" \
  -o -name "*.arb" -o -name "*.po" -o -name "messages*.properties" \) | xargs -0 -n1 echo
srcfiles \( -path "*i18n*" -o -path "*locale*" -o -path "*locales*" -o -path "*translations*" \) -name "*.json" \
  | xargs -0 -n1 echo
# Then resolve one key: the throw site, and the catalog line
grep -rnH --exclude-dir=node_modules "orders.too_many_items" "$R"
```

- Resolved → quote the sentence exactly, cite **both** the throw site and
  the catalog line (`S1:23, S3:7` in the spec; both columns in
  `evidence.md`).
- Several languages → quote the default (neutral) catalog and note the
  others exist.
- Not found → write the key as ``key `orders.not_found` (unresolved)``,
  label 🟡, add a Gap row and an open question. Never write a sentence
  the catalog doesn't contain.
- Wording assembled at runtime (string interpolation) → quote the
  template with its placeholder: `"An order can hold at most {0} items."`.

## D. Dead code, flags and deprecated paths

A route nobody calls, an endpoint marked obsolete, or a feature behind a
flag that is off must not be written up as a live capability.

```bash
srcfiles | xargs -0 grep -nH -E "\[Obsolete|@Deprecated|@deprecated|@available\(\*, *deprecated|// *DEPRECATED" | head -40
srcfiles | xargs -0 grep -nH -E "if *\( *false *\)|FeatureFlag|IsEnabled\(|isEnabled\(|feature[._-]?flag|FEATURE_|ENABLE_" | head -40
# No caller: take each backend path, search the client submodules for it
grep -rnH --exclude-dir=node_modules "orders/legacy" src/shop-app
```

- Suspected dead or flagged-off → 🟡, an open question ("still used?"),
  and a Gap row with the pattern and scope searched.
- No caller in the submodules you have is not proof of no caller at all:
  another client may exist outside the tracking repo. Say so in the open
  question.

## H. Cross-repo hops

When one action in one submodule triggers work in another (a screen
calls an endpoint; an API writes a queue message a worker reads), record
the hop in `evidence.md` with a citation on **each** side.

```bash
# Client side: base URLs, path constants, HTTP calls
srcfiles | xargs -0 grep -nH -E "https?://|baseUrl|BASE_URL|/api/|fetch\(|axios|HttpClient|URLSession|Retrofit|dio\." | head -60
# Messaging and storage hand-offs
srcfiles | xargs -0 grep -nH -E "Queue|Topic|Publish|Subscribe|ServiceBus|Kafka|RabbitMQ|SQS|SNS|BlobContainer|S3" | head -40
```

- Match the client's path (`/api/orders`) to the server's route
  (`[Route("api/orders")]`) before calling it a hop. A name match alone is
  not enough.
- One side only → it's a Gap ("calls an external service at `<url>`"),
  not a hop.

## Unknown stack

No stack file fits: read the manifest and entry point, then search for
the stack's own routing words (`route`, `router`, `handler`,
`controller`, `screen`, `page`, `command`). Say in the report that
coverage is lower because no recipe exists for that stack.
