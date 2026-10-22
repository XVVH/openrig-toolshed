"""Pin 3: one classify-before-ask bullet inserted in lead.md and in builder.md.

Ask, 'What it is' 2 and 'Done looks like' 3: one inserted line in lead.md's
"Scope the work" and in builder.md, before the existing "ask" step. A fact
observable by running something routes to prototype-before-ask; a product or
preference call still goes to a human (the person, or for the builder the lead).
Constraints: a visual fork still falls through to asking -- never silently decided.
"""
import difflib
import os
import re
import unittest

import _support as S

CASES = {
    "lead": {
        "rel": "agents/toolshed/guidance/lead.md",
        "section": "## Scope the work",
        "before": "- If two readings lead to different work, ask the person in one line",
        "asks": "the person",
    },
    "builder": {
        "rel": "agents/toolshed/guidance/builder.md",
        "section": "## Make the change",
        "before": "- Something you notice outside the brief goes to the lead as one note",
        "asks": "the lead",
    },
}


def _ws(s):
    return re.sub(r"\s+", " ", s).strip()


def _insertion(case):
    """Return (ours_lines, start, end) of the single inserted block, or fail."""
    up = S.rename(S.read_text(S.upstream_path(case["rel"]))).splitlines()
    ours = S.read_text(os.path.join(S.TOOLSHED, case["rel"])).splitlines()
    ops = [op for op in difflib.SequenceMatcher(None, up, ours, autojunk=False).get_opcodes()
           if op[0] != "equal"]
    return up, ours, ops


class GuidanceInsertion(unittest.TestCase):
    def _check_shape(self, name):
        case = CASES[name]
        up, ours, ops = _insertion(case)
        self.assertEqual(
            [op[0] for op in ops], ["insert"],
            "%s must differ from upstream (after the rename) by exactly one insertion; got %r"
            % (case["rel"], ops))
        _, i1, _, j1, j2 = ops[0]
        block = ours[j1:j2]
        # strip blank lines around the insertion
        while block and not block[0].strip():
            block, j1 = block[1:], j1 + 1
        while block and not block[-1].strip():
            block, j2 = block[:-1], j2 - 1
        self.assertTrue(block, "inserted block is empty")
        self.assertTrue(block[0].startswith("- "), "insertion must be a bullet: %r" % block[0])
        for line in block[1:]:
            self.assertFalse(line.startswith("- ") or not line.startswith(" "),
                             "insertion must be exactly one bullet; extra line %r" % line)

        # Section: the nearest heading above the insertion.
        headings = [l for l in ours[:j1] if l.startswith("## ")]
        self.assertTrue(headings)
        self.assertEqual(headings[-1].strip(), case["section"])

        # The existing ask-bullet comes after the insertion, in the same section.
        rest = ours[j2:]
        section_rest = []
        for line in rest:
            if line.startswith("## "):
                break
            section_rest.append(line)
        starts = [l for l in section_rest if _ws(l).startswith(case["before"])]
        self.assertEqual(len(starts), 1,
                         "%r must follow the inserted bullet inside %s"
                         % (case["before"], case["section"]))
        return S.norm(" ".join(block))

    def _check_text(self, name, text):
        case = CASES[name]
        self.assertIn("prototype-before-ask", text)
        self.assertRegex(text, r"\bobserv\w*\b[^.]{0,60}\brun(ning)?\b",
                         "must say the fact is observable by running something")
        self.assertRegex(text, r"\b(settle|resolve|decide)\w*\b[^.]{0,40}\b(in this seat|in the seat|yourself|inline)\b",
                         "must say such a fork is settled in the seat, not asked")
        visual = [s for s in S.sentences(text) if "visual" in s]
        self.assertTrue(visual, "must name visual forks")
        self.assertTrue(
            any(re.search(r"\bpreference\b", s) and re.search(r"\bproduct\b", s)
                and case["asks"] in s for s in visual),
            "the same sentence must send a product/preference call and anything visual to %s: %r"
            % (case["asks"], visual))

    def test_lead_inserts_one_bullet_in_scope_the_work(self):
        self._check_shape("lead")

    def test_lead_bullet_classifies_before_asking(self):
        self._check_text("lead", self._check_shape("lead"))

    def test_builder_inserts_one_bullet_in_make_the_change(self):
        self._check_shape("builder")

    def test_builder_bullet_classifies_before_asking(self):
        self._check_text("builder", self._check_shape("builder"))


if __name__ == "__main__":
    unittest.main()
