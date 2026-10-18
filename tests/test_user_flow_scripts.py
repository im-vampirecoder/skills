"""Tests for skills/delivery/vc-define-user-flow/scripts against tests/fixtures/user-flow-repo.

    python3 -m unittest discover -s tests -p "test_*.py"

The fixture map passes every level; each failing case is one edit to it.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "delivery" / "vc-define-user-flow" / "scripts"
FIXTURE = HERE / "fixtures" / "user-flow-repo"
sys.path.insert(0, str(SCRIPTS))

import check_user_flow  # noqa: E402
import user_flow_parse  # noqa: E402


class UserFlowCheckTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(FIXTURE, self.root)
        self.flow = self.root / "artifacts" / "checkout" / "ux" / "user-flow.md"
        self.prd = self.root / "artifacts" / "checkout" / "prd.md"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def edit(self, path, old, new):
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def errors(self):
        result = check_user_flow.run(self.flow, self.prd, compile_diagram=False)
        return {(level, f[1]) for level, fs in result["levels"].items() if fs for f in fs if f[0] == "error"}

    def test_fixture_passes(self):
        self.assertEqual(self.errors(), set())
        run = subprocess.run([sys.executable, str(SCRIPTS / "check_user_flow.py"), "check", str(self.flow),
                              "--prd", str(self.prd), "--no-compile"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        for level in ("structure: ok", "renderer: ok", "consistency: ok", "requirements: ok",
                      "compile: skipped", "business correctness: not machine-checked"):
            self.assertIn(level, run.stdout)

    def test_unlabelled_branch(self):
        self.edit(self.flow, 'D1 -->|"No, tries left"| S4', "D1 --> S4")
        self.assertIn(("structure", "unlabelled-branch"), self.errors())

    def test_dead_end(self):
        self.edit(self.flow, '  S4 -->|"Try another card"| S2\n', "")
        self.edit(self.flow, "| S4 Card declined | S2 Payment | taps Try another card | — | — |\n", "")
        self.assertEqual(self.errors(), {("structure", "dead-end")})

    def test_temporary_state_needs_a_way_out(self):
        self.edit(self.flow, "class S3 terminal", "class S3,S5 terminal")
        self.edit(self.flow, '  S5 -->|"Back to cart"| S1\n', "")
        self.edit(self.flow, "| S5 Locked: try later | S1 Cart | taps Back to cart | — | — |\n", "")
        self.assertIn(("structure", "temporary-trap"), self.errors())

    def test_table_and_diagram_drift(self):
        self.edit(self.flow, "| S5 Locked: try later | S1 Cart | taps Back to cart | — | — |\n", "")
        self.edit(self.flow, "| 4 | card-declined |", "| 6 | card-declined |")
        errors = self.errors()
        self.assertIn(("consistency", "edge-missing-row"), errors)
        self.assertIn(("consistency", "screen-missing-row"), errors)
        self.assertIn(("consistency", "screen-missing-node"), errors)

    def test_unquoted_label(self):
        self.edit(self.flow, 'S5["[5] Locked: try later"]', "S5[Locked: try later]")
        self.assertIn(("renderer", "unquoted-label"), self.errors())

    def test_html_entity_and_newline_escape(self):
        self.edit(self.flow, '"[3] Order confirmed"', '"[3] Order &amp; receipt\\nsent"')
        errors = self.errors()
        self.assertIn(("renderer", "html-entity"), errors)
        self.assertIn(("renderer", "newline-escape"), errors)

    def test_uncovered_p0_fr(self):
        self.edit(self.flow, "| Review items and total | new | pay | FR-checkout.review-cart |",
                  "| Review items and total | new | pay | — |")
        self.edit(self.flow, "| taps Checkout | cart not empty | FR-checkout.review-cart |",
                  "| taps Checkout | cart not empty | — |")
        self.assertEqual(self.errors(), {("requirements", "uncovered-p0")})

    def test_uncovered_user_facing_err(self):
        self.edit(self.flow, "| bank declines | tries left | ERR-checkout.card-declined |",
                  "| bank declines | tries left | — |")
        self.assertEqual(self.errors(), {("requirements", "uncovered-err")})

    def test_retired_id_cited(self):
        self.edit(self.flow, "| bank approves | — | FR-checkout.pay-with-card |",
                  "| bank approves | — | FR-checkout.pay-with-stripe |")
        self.assertIn(("requirements", "dead-id"), self.errors())

    def test_new_prd_requirement_makes_map_stale(self):
        self.edit(self.prd, "### Business rules",
                  "- **FR-checkout.apply-coupon** (P1): When the customer enters a coupon, the system shall apply it.\n\n### Business rules")
        self.assertEqual(self.errors(), {("requirements", "requirements-stale")})

    def test_hash_covers_sections_1_to_4_only(self):
        before = user_flow_parse.load_map(self.flow)["hash"]
        self.edit(self.flow, "Assumed: per card", "Assumed: per customer")
        self.assertEqual(user_flow_parse.load_map(self.flow)["hash"], before)
        self.edit(self.flow, "Review items and total", "Review the items and total")
        self.assertNotEqual(user_flow_parse.load_map(self.flow)["hash"], before)

    def test_approved_map_with_old_hash_is_stale(self):
        self.edit(self.flow, "status: draft", "status: approved")
        self.edit(self.flow, "flow_hash:\n", "flow_hash: 0000000000000000\n")
        result = check_user_flow.run(self.flow, self.prd, compile_diagram=False)
        self.assertIn("stale", result["approval"])


if __name__ == "__main__":
    unittest.main()
