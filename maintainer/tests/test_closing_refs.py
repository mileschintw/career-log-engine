#!/usr/bin/env python3
"""Tests for .github/workflows/closing_refs.py's check(), on made-up bodies; nothing reaches GitHub.

  python3 -I maintainer/tests/test_closing_refs.py
"""
import importlib.util, os, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "..", ".github", "workflows", "closing_refs.py")
spec = importlib.util.spec_from_file_location("closing_refs", TOOL)
closing_refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closing_refs)

REPO = "owner/repo"


class Check(unittest.TestCase):
    def test_draft_and_pr_modes(self):
        body = "Closes #12\n\nfixes #86\n"
        self.assertEqual(len(closing_refs.check(REPO, body)), 1)
        kinds = {12: "issue"}
        problems = closing_refs.check(REPO, body, {(REPO, 12), (REPO, 86)}, kinds.get)
        self.assertEqual(len(problems), 2)
        self.assertIn("GitHub will close #86, which has no `Closes #86` line", problems[1])


if __name__ == "__main__":
    unittest.main()
