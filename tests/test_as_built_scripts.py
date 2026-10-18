"""Tests for skills/delivery/vc-code-to-srs/scripts against tests/fixtures/as-built-repo.

    python3 -m unittest discover -s tests -p "test_*.py"

The fixture pack passes every level; each failing case is one edit to it.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "delivery" / "vc-code-to-srs" / "scripts"
REQUIREMENTS = HERE.parent / "skills" / "delivery" / "vc-requirements" / "scripts"
FIXTURE = HERE / "fixtures" / "as-built-repo"
sys.path.insert(0, str(SCRIPTS))

import as_built_plan  # noqa: E402
import check_as_built  # noqa: E402


class AsBuiltCheckTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(FIXTURE, self.root)
        self.pack = self.root / "artifacts" / "checkout" / "as-built"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def edit(self, name, old, new):
        path = self.pack / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def errors(self):
        result = check_as_built.run(self.pack, compile_diagram=False)
        return {(level, f[1]) for level, fs in result["levels"].items() if fs for f in fs if f[0] == "error"}

    def test_fixture_passes(self):
        self.assertEqual(self.errors(), set())
        run = subprocess.run([sys.executable, str(SCRIPTS / "check_as_built.py"), "check", str(self.pack),
                              "--no-compile"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        for level in ("structure: ok", "citations: ok", "ids: ok", "renderer: ok", "self-containment: ok",
                      "compile: skipped", "business correctness: not machine-checked", "labels: ✅ 22 · 🔵 1 · 🟡 4"):
            self.assertIn(level, run.stdout)

    def test_missing_label(self):
        self.edit("spec.md", "| Shows the order, or a not-found message when it doesn't exist | ✅ |",
                  "| Shows the order, or a not-found message when it doesn't exist | yes |")
        self.assertIn(("structure", "missing-label"), self.errors())

    def test_asserted_claim_without_source(self):
        self.edit("spec.md", "| Every order action requires a signed-in customer. | ✅ | S1:10 |",
                  "| Every order action requires a signed-in customer. | ✅ | - |")
        self.assertIn(("structure", "missing-citation"), self.errors())

    def test_bare_basename(self):
        self.edit("evidence.md", "`src/shop-api/Validators/PlaceOrderValidator.cs:12`", "`PlaceOrderValidator.cs:12`")
        self.assertIn(("citations", "bare-basename"), self.errors())

    def test_citation_past_end_of_file(self):
        self.edit("evidence.md", "`src/shop-api/Domain/Order.cs:25`", "`src/shop-api/Domain/Order.cs:250`")
        self.assertEqual(self.errors(), {("citations", "line-range")})

    def test_source_row_range_past_end_of_file(self):
        self.edit("spec.md", "| S1:31-36 |", "| S1:31-99 |")
        self.assertEqual(self.errors(), {("citations", "line-range")})

    def test_named_id_in_pack(self):
        self.edit("use-cases/uc-place-order.md", "FR1, BR1, BR2", "FR-checkout.place-order, BR1, BR2")
        self.assertIn(("ids", "named-id"), self.errors())

    def test_undefined_alias(self):
        self.edit("use-cases/uc-cancel-order.md", "FR3, BR4, ERR3", "FR3, BR4, ERR9")
        self.assertEqual(self.errors(), {("ids", "undefined-id")})

    def test_flow_without_sequence(self):
        self.edit("flows.md", "sequenceDiagram\n    actor Customer\n    participant Shop as Shop service",
                  "flowchart LR\n    X --> Y")
        self.assertIn(("renderer", "flow-diagrams"), self.errors())

    def test_semicolon_in_message(self):
        self.edit("flows.md", "Customer->>App: Taps Place order", "Customer->>App: Taps Place order; waits")
        self.assertEqual(self.errors(), {("renderer", "semicolon")})

    def test_unquoted_flowchart_label(self):
        self.edit("flows.md", 'C -->|"No"| D["Save order as Placed"]', 'C -->|"No"| D[Save order: Placed]')
        self.assertEqual(self.errors(), {("renderer", "unquoted-label")})

    def test_unresolved_key_shown_as_asserted(self):
        self.edit("spec.md", "| key `orders.not_found` (unresolved) | FR2 | 🟡 |",
                  "| key `orders.not_found` (unresolved) | FR2 | ✅ |")
        self.edit("spec.md", "asserted: 22", "asserted: 23")
        self.edit("spec.md", "inferred: 4", "inferred: 3")
        self.assertEqual(self.errors(), {("ids", "unresolved-wording")})

    def test_skipped_test_cited_as_asserted(self):
        self.edit("spec.md", "| A customer can cancel an order that hasn't shipped yet. | ✅ | S1:38-50 |",
                  "| A customer can cancel an order that hasn't shipped yet. | ✅ | S6:15-16 |")
        self.edit("spec.md", "| S6 | src/shop-api/tests/OrdersControllerTests.cs | 8-13 |",
                  "| S6 | src/shop-api/tests/OrdersControllerTests.cs | 8-20 |")
        self.assertEqual(self.errors(), {("citations", "skipped-test")})

    def test_tool_name_in_output(self):
        self.edit("spec.md", "# Checkout - as built", "# Checkout - as built (generated by vc)")
        self.assertIn(("self-containment", "tool-reference"), self.errors())

    def test_invisible_character(self):
        self.edit("erd.md", "One purchase by one customer", "One purchase\u200b by one customer")
        self.assertEqual(self.errors(), {("self-containment", "invisible-char")})

    def test_label_counts_must_match(self):
        self.edit("spec.md", "asserted: 22", "asserted: 21")
        self.assertEqual(self.errors(), {("structure", "label-count")})

    def test_single_source_corroboration(self):
        self.edit("spec.md", "| 🔵 | S4:20, S4:6 |", "| 🔵 | S4:20 |")
        self.assertEqual(self.errors(), {("structure", "corroboration")})

    def test_unlisted_use_case(self):
        (self.pack / "use-cases" / "uc-ship-order.md").write_text("# Ship an order\n", encoding="utf-8")
        self.assertEqual(self.errors(), {("ids", "unlisted-use-case")})

    def test_hop_needs_two_submodules(self):
        self.edit("evidence.md", "| `src/shop-app/src/screens/CheckoutScreen.tsx:10` |",
                  "| `src/shop-api/Controllers/OrdersController.cs:23` |")
        self.assertEqual(self.errors(), {("structure", "hop-evidence")})

    def requirement_findings(self):
        run = subprocess.run([sys.executable, str(REQUIREMENTS / "check_requirement_ids.py"), "--root",
                              str(self.root), "--json"], capture_output=True, text=True, cwd=REQUIREMENTS)
        self.assertIn(run.returncode, (0, 1), run.stderr)
        return json.loads(run.stdout)["findings"]

    def test_requirements_checker_ignores_local_ids(self):
        self.assertEqual(self.requirement_findings(), [])

    def test_requirements_checker_would_flag_named_ids(self):
        self.edit("use-cases/uc-place-order.md", "FR1, BR1, BR2", "FR-checkout.place-order, BR1, BR2")
        self.assertIn("dangling", {f["check"] for f in self.requirement_findings()})


class AsBuiltPlanTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(FIXTURE, self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def plan(self, **changes):
        plan = as_built_plan.load(self.root)
        plan["features"][0].update(changes)
        return as_built_plan.validate(self.root, plan)

    def test_fixture_plan_is_valid(self):
        self.assertEqual(self.plan(), [])

    def test_reserved_slug(self):
        errors = self.plan(slug="as-built-plan", feature_id="FEATURE-as-built-plan", existing_prd=None)
        self.assertTrue(any("reserved slug" in e for e in errors), errors)

    def test_collision_with_existing_prd(self):
        errors = self.plan(existing_prd=None)
        self.assertTrue(any("set existing_prd" in e for e in errors), errors)

    def test_entry_without_source(self):
        self.assertTrue(any("at least one source" in e for e in self.plan(sources=[])))

    def test_source_outside_submodule_root(self):
        self.assertTrue(any("not an existing path" in e for e in self.plan(sources=["docs/x.md"])))

    def test_init_keeps_done_status_and_adds_new(self):
        candidates = self.root / "candidates.json"
        candidates.write_text(json.dumps({"features": [
            {"slug": "checkout", "title": "Checkout", "feature_id": "FEATURE-checkout",
             "sources": ["src/shop-api/Controllers/OrdersController.cs"], "existing_prd": "artifacts/checkout/prd.md"},
            {"slug": "order-history", "title": "Order history", "feature_id": "FEATURE-order-history",
             "sources": ["src/shop-api/Controllers/OrdersController.cs"], "existing_prd": None}]}), encoding="utf-8")
        run = subprocess.run([sys.executable, str(SCRIPTS / "as_built_plan.py"), "--root", str(self.root), "init",
                              "--from", str(candidates)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        saved = {f["slug"]: f["status"] for f in as_built_plan.load(self.root)["features"]}
        self.assertEqual(saved, {"checkout": "done", "order-history": "pending"})


if __name__ == "__main__":
    unittest.main()
