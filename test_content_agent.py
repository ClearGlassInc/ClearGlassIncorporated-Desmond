import unittest

from content_agent import ALLOCATION, PILLARS, build_plan, validate_seed


SEED = {
    "opacity_issue": "missing public records", "security_consequence": "controls cannot be verified",
    "founder_truth": "I rebuilt the evidence model today.", "product": "Guardian",
    "feature": "evidence mapping", "pain": "unowned risk", "demo": "map evidence to an owner",
    "sources": ["https://example.gov/report"]
}


class ContentAgentTests(unittest.TestCase):
    def test_exact_allocation_and_approval_gate(self):
        drafts = build_plan(SEED)
        self.assertEqual(len(drafts), 10)
        self.assertEqual([sum(d.pillar == p for d in drafts) for p in PILLARS], list(ALLOCATION))
        self.assertTrue(all(d.status == "DRAFT_REQUIRES_HUMAN_APPROVAL" for d in drafts))

    def test_clarity_drafts_retain_sources(self):
        drafts = build_plan(SEED)
        self.assertTrue(all(d.evidence == SEED["sources"] for d in drafts[:5]))

    def test_rejects_missing_or_non_https_sources(self):
        bad = dict(SEED, sources=[])
        with self.assertRaises(ValueError):
            validate_seed(bad)
        bad["sources"] = ["http://example.gov/report"]
        with self.assertRaises(ValueError):
            validate_seed(bad)


if __name__ == "__main__":
    unittest.main()
