"""Tests for skills/delivery/vc-requirements/scripts against tests/fixtures/requirements-repo.

    python3 -m unittest discover -s tests -p "test_*.py"
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "delivery" / "vc-requirements" / "scripts"
PRD_SCRIPTS = HERE.parent / "skills" / "delivery" / "vc-prd" / "scripts"
FIXTURE = HERE / "fixtures" / "requirements-repo"
sys.path.insert(0, str(SCRIPTS))

import check_requirement_ids  # noqa: E402
import parse_requirement_ids  # noqa: E402
import requirement_state  # noqa: E402
import shortlist_conflict_candidates  # noqa: E402


def run_script(name, root, *extra):
    return subprocess.run([sys.executable, str(SCRIPTS / name), "--root", str(root), *extra],
                          capture_output=True, text=True)


class RequirementScriptsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(FIXTURE, self.root)

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def checks(self):
        findings, _, _ = check_requirement_ids.run(self.root)
        return {(f["check"], f["id"]) for f in findings if f["level"] == "error"}

    def test_fixture_errors(self):
        errors = self.checks()
        self.assertIn(("dangling", "FR-checkout.no-such-thing"), errors)
        self.assertIn(("malformed", "FR-Bad.Name"), errors)
        self.assertEqual(run_script("check_requirement_ids.py", self.root).returncode, 1)

    def test_frozen_text_edit_is_an_error(self):
        self.assertEqual(run_script("build_requirements_view.py", self.root).returncode, 0)
        prd = self.root / "artifacts" / "checkout" / "prd.md"
        prd.write_text(prd.read_text().replace("charge the card through Stripe", "charge the card"))
        self.assertIn(("frozen-edited", "FR-checkout.pay-with-stripe"), self.checks())
        # Rebuilding the view must not launder the edit into the baseline.
        run_script("build_requirements_view.py", self.root)
        self.assertIn(("frozen-edited", "FR-checkout.pay-with-stripe"), self.checks())

    def test_retiring_a_frozen_id_is_not_an_edit(self):
        run_script("build_requirements_view.py", self.root)
        prd = self.root / "artifacts" / "checkout" / "prd.md"
        old = "charge the card through Stripe."
        prd.write_text(prd.read_text().replace(old, old + " Retired. Replaced by FR-checkout.guest-pay."))
        self.assertNotIn(("frozen-edited", "FR-checkout.pay-with-stripe"), self.checks())

    def test_draft_is_seen_by_shortlist_but_not_by_check(self):
        folder = self.root / "artifacts" / "gift-cards"
        folder.mkdir()
        (folder / "prd.draft.md").write_text(
            "---\nid: FEATURE-gift-cards\nstatus: draft\n---\n\n## Requirements\n\n### Business rules\n"
            "- **BR-gift-cards.max-retry-per-card:** A gift card can be tried at most 2 times.\n")
        self.assertEqual(self.checks(), {("dangling", "FR-checkout.no-such-thing"), ("malformed", "FR-Bad.Name")})
        pairs = shortlist_conflict_candidates.shortlist(self.root, feature="gift-cards")["pairs"]
        self.assertTrue(any("BR-gift-cards.max-retry-per-card" in (p["a"], p["b"]) for p in pairs))

    def test_open_story_citing_retired_id(self):
        story = self.root / "artifacts" / "checkout" / "stories-2-guest.md"
        story.write_text(story.read_text().replace("FR-checkout.no-such-thing", "FR-accounts.old-sign-in"))
        self.assertIn(("retired-but-cited", "FR-accounts.old-sign-in"), self.checks())

    def test_view_states(self):
        out = run_script("build_requirements_view.py", self.root, "--stdout").stdout
        self.assertIn("being replaced by FEATURE-paypal-checkout (draft)", out)
        self.assertIn("retired (replaced by FR-accounts.sign-in-with-email)", out)
        self.assertIn("P0 FRs with no story: FR-checkout.show-receipt", out)
        self.assertIn("clarified 1x", out)
        self.assertIn("vc-frozen-baseline", out)

    def test_shortlist_pairs_and_skips_dismissed(self):
        pairs = shortlist_conflict_candidates.shortlist(self.root, feature=None)
        keys = {frozenset((p["a"], p["b"])) for p in pairs["pairs"]}
        self.assertIn(frozenset(("FR-checkout.guest-pay", "BR-accounts.login-before-purchase")), keys)
        self.assertIn(frozenset(("BR-checkout.max-retry-per-card", "BR-card-wallet.max-retry-per-card")), keys)
        self.assertIn(frozenset(("NFR-checkout.payment-response-time", "NFR-card-wallet.payment-response-time")), keys)
        self.assertNotIn(frozenset(("FR-checkout.show-receipt", "FR-card-wallet.show-receipt")), keys)
        for p in pairs["pairs"]:
            self.assertFalse(p["a_status"] == p["b_status"] == "done")
        bugs = {frozenset((p["a"], p["b"])) for p in pairs["bug_candidates"]}
        self.assertIn(frozenset(("BR-loyalty.guest-points", "BR-accounts.login-before-purchase")), bugs)

    def test_done_and_legacy_delivered_both_read_as_done(self):
        features = {f["slug"]: f for f in parse_requirement_ids.load_project(self.root)["features"]}
        self.assertEqual(features["accounts"]["status"], "done")
        self.assertEqual(features["loyalty"]["status"], "done")
        for slug in ("accounts", "loyalty"):
            definition = features[slug]["definitions"][0]
            self.assertEqual(requirement_state.frozen_reason(features[slug], definition), "feature done")

    def test_shortlist_scoped_to_one_feature(self):
        pairs = shortlist_conflict_candidates.shortlist(self.root, feature="card-wallet")
        for p in pairs["pairs"]:
            self.assertIn("card-wallet", (p["a_feature"], p["b_feature"]))

    def test_apply_supersessions_is_idempotent(self):
        cmd = [sys.executable, str(PRD_SCRIPTS / "apply_supersessions.py"), "--root", str(self.root),
               "--feature", "paypal-checkout", "--date", "2026-10-17"]
        subprocess.run(cmd, check=True, capture_output=True)
        subprocess.run(cmd, check=True, capture_output=True)
        text = (self.root / "artifacts" / "checkout" / "prd.md").read_text()
        self.assertEqual(text.count("> Superseded by FR-paypal-checkout.pay-with-paypal on 2026-10-17"), 1)
        self.assertIn("superseded: [FR-checkout.pay-with-stripe]", text)
        out = run_script("build_requirements_view.py", self.root, "--stdout").stdout
        self.assertIn("superseded by FR-paypal-checkout.pay-with-paypal", out)


if __name__ == "__main__":
    unittest.main()
