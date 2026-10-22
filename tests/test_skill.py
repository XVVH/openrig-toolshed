"""Pin 4: the prototype-before-ask skill says what the ask's port requires.

Ask, 'What it is' 1 and 3, and Constraints: behavioural/timing half of pstack's
Prototype playbook only; no decision -> no prototype; scratch dir kept out of
commits via .git/info/exclude, in the seat's own checkout; alternatives run
labelled side by side; observe, don't assert; report = variants, evidence,
recommendation, scratch path, throwaway; the round never crosses seats -- only
the outcome, tagged kind:prototype-decision; no visual decisions, no
screenshot/browser tool, a visual fork goes to the person.
Assertions are regexes over whitespace-normalised text, not prose snapshots.
"""
import os
import re
import unittest

import yaml

import _support as S

SKILL = os.path.join(S.TOOLSHED, S.SKILL_REL)


def _split():
    raw = S.read_text(SKILL)
    m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", raw, re.S)
    if not m:
        raise AssertionError("SKILL.md must open with a YAML frontmatter block")
    return yaml.safe_load(m.group(1)), m.group(2)


class Frontmatter(unittest.TestCase):
    def test_name(self):
        fm, _ = _split()
        self.assertEqual(fm.get("name"), "prototype-before-ask")

    def test_description_names_the_trigger(self):
        fm, _ = _split()
        d = S.norm(str(fm.get("description", "")))
        self.assertRegex(d, r"\b(about to ask|before (you )?ask(ing)?)\b")
        self.assertRegex(d, r"\b(approach|behaviou?r|timing)\b")
        self.assertRegex(d, r"\brun(ning)?\b", "trigger: answerable by running something")


class Body(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, body = _split()
        cls.t = S.norm(body)
        cls.sents = S.sentences(cls.t)

    def _any_sentence(self, *patterns):
        return any(all(re.search(p, s) for p in patterns) for s in self.sents)

    def test_no_decision_no_prototype(self):
        self.assertRegex(self.t, r"\bno (real |actual )?decision\b[^.]{0,80}\bno prototype\b")

    def test_scratch_dir_in_the_seats_checkout_never_the_source_tree(self):
        # Skill 1.1: the scratch dir sits in the checkout the seat works in -- the clone
        # for the lead, the builder's own worktree for the builder.
        where = re.search(r"\bscratch\b.{0,120}?\b(root of|in|inside|under) (the |your |whichever |each )?"
                          r"(own )?(checkout|working copy) (that )?(you|the seat|this seat|each seat|it)"
                          r"( (are|is))? (work(s|ing)?|stand(s|ing)?)\b", self.t)
        self.assertTrue(where, "the scratch dir must be in the checkout the seat works in")
        after = self.t[where.end():where.end() + 250] if where else ""
        self.assertRegex(after, r"\bclone\b[^.;]{0,40}\blead\b|\blead\b[^.;]{0,40}\bclone\b",
                         "for the lead, that checkout is the clone")
        self.assertRegex(after, r"\bworktree\b[^.;]{0,40}\bbuilder\b|\bbuilder\b[^.;]{0,40}\bworktree\b",
                         "for the builder, that checkout is its own worktree")
        self.assertRegex(self.t, r"\bscratch\b.{0,400}\b(never|not)\b[^.]{0,20}\b(in|inside|under|part of) "
                                 r"(the |your )?((repository|repo|project)'s )?source tree\b",
                         "the scratch dir is never in the repository's source tree")
        # The pre-1.1 rule is gone.
        self.assertNotRegex(self.t, r"\bscratch\b.{0,240}\b(never|not)\b[^.]{0,30}\b(your|the seat's|its|this seat's) (own )?worktree\b",
                            "must no longer say the scratch dir is never the seat's own worktree")

    def test_scratch_dir_excluded_via_clone_git_info_exclude_covering_worktrees(self):
        self.assertIn("/.scratch/", self.t)
        self.assertRegex(self.t, r"\b(clone's|shared) \.git/info/exclude\b|\.git/info/exclude (of|in) the clone\b",
                         "the exclude line goes in the clone's .git/info/exclude")
        self.assertRegex(self.t, r"\.git/info/exclude\b.{0,120}?\b(covers?|applies to|appl(y|ies) (to|in)|shared (by|with|across))\b"
                                 r"[^.]{0,30}\b(every|all|each|the) (\w+ )?worktrees?\b",
                         "that one exclusion covers every worktree")
        self.assertRegex(self.t, r"\b(out of|never in|not in|kept from) (the )?commits?\b|\bnever committed\b")

    def test_alternatives_run_labelled_side_by_side(self):
        self.assertTrue(self._any_sentence(r"\blabel(l)?ed\b|\blabels?\b", r"side[- ]by[- ]side"))

    def test_observe_not_assert(self):
        self.assertIn("the observation is the test", self.t)
        self.assertRegex(self.t, r"\b(don't|do not|not|rather than|instead of|never) assert")
        self.assertRegex(self.t, r"\b(print|log)\w*\b")

    def test_report_has_variants_evidence_recommendation_scratch_path_throwaway(self):
        need = [r"\b(variants?|alternatives?)\b", r"\bevidence\b", r"\brecommend\w*\b",
                r"\bscratch (path|dir\w*)\b|\bpath (to|of) the scratch\b", r"\bthrowaway\b"]
        ok = False
        for m in re.finditer(r"\breport\b", self.t):
            window = self.t[m.start():m.start() + 800]
            if all(re.search(p, window) for p in need):
                ok = True
                break
        self.assertTrue(ok, "a report passage must name variants, evidence, recommendation, "
                            "scratch path and 'throwaway'")

    def test_round_never_crosses_seats_as_a_queue_item(self):
        self.assertTrue(self._any_sentence(r"\b(never|not|no)\b", r"\bqueue\b",
                                           r"\b(round|prototype)\b"),
                        "must say the prototype round itself is never a queue item")
        # resolved inline: in the seat holding the thread, not handed off
        self.assertRegex(self.t, r"\b(inline|in that seat|in this seat|in the same seat)\b")

    def test_lead_resolves_into_brief_builder_into_report_to_review_and_qa(self):
        self.assertRegex(self.t, r"\blead\b[^.]{0,160}\bbrief\b")
        self.assertRegex(self.t, r"\bbuild\w*\b[^.]{0,200}\breport\b[^.]{0,120}\breview\w*\b")
        self.assertRegex(self.t, r"\bbuild\w*\b[^.]{0,200}\breport\b[^.]{0,160}\bqa\b")

    def test_only_the_outcome_crosses_tagged_prototype_decision(self):
        self.assertIn("kind:prototype-decision", self.t)
        self.assertRegex(self.t, r"\bonly the (outcome|decision|result)\b")

    def test_visual_fork_goes_to_the_person(self):
        # Visual falls through to asking (the person, or via the lead) and is never decided silently.
        self.assertRegex(self.t, r"\bvisual\b[^#]{0,120}\bask\b",
                         "a visual fork must be asked, not prototyped")
        self.assertRegex(self.t, r"\bvisual\b[^#]{0,250}\bnever\b[^.]{0,30}\bsilently\b|\bvisual\b[^.]{0,120}\bperson\b",
                         "a visual fork is never decided silently")

    def test_names_no_screenshot_or_browser_tool(self):
        tools = r"\b(playwright|puppeteer|selenium|webdriver|cypress|chromedp|devtools|" \
                r"browser[-_ ]use|agent-browser|capture_screenshot|screencapture)\b"
        self.assertNotRegex(self.t, tools)
        for s in self.sents:
            if re.search(r"\b(screenshots?|browsers?)\b", s):
                self.assertRegex(s, r"\b(no|not|never|without|out of scope)\b",
                                 "screenshot/browser may only appear as an exclusion: %r" % s)


if __name__ == "__main__":
    unittest.main()
