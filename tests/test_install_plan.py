"""Pin 7: the install preview on the-claw plans cleanly and writes the skill to lead and builder.

Ask, 'Done looks like' 4: `rig bundle install ... --preset recommended --plan`
previews cleanly (no schema errors). OpenRig (`rig` 0.6.14) lives on the-claw;
this test syncs rigs/ to /tmp there, builds the bundle and runs the read-only
--plan install. Nothing under ~/rigs on the-claw is touched. Skipped when
`ssh claw-auto` is not reachable so the suite stays green offline.
"""
import os
import re
import subprocess
import unittest

import _support as S

HOST = "claw-auto"
REMOTE = (
    "export PATH=/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:$PATH; "
    "cd /tmp/toolshed-check/src && "
    "rig bundle create rigs/toolshed/rig.yaml --preset recommended "
    "--min-cli-version 0.6.6 --min-daemon-version 0.6.6 -o /tmp/toolshed-check/toolshed.rigbundle && "
    "cd /tmp/toolshed-check/proj && "
    "rig bundle install /tmp/toolshed-check/toolshed.rigbundle --target /tmp/toolshed-check/target --cwd . --plan"
)
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8"]
SKILL_ID = "prototype-before-ask"
CONTEXT_CMD = "rig context add --git https://github.com/mvschwarz/openrig-world"


def _reachable():
    try:
        return subprocess.run(SSH + [HOST, "true"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _seats():
    """dotted seat id -> profile, from rig.yaml."""
    rig = S.load_yaml(os.path.join(S.TOOLSHED, "rig.yaml"))
    return {"%s.%s" % (p["id"], m["id"]): m["profile"]
            for p in rig["pods"] for m in p.get("members", [])}


@unittest.skipUnless(_reachable(), "ssh %s unreachable; install preview not run" % HOST)
class InstallPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # --delete keeps the remote copy equal to this checkout (only /tmp on the-claw).
        subprocess.run(
            ["rsync", "-a", "--delete", "--exclude", ".git",
             os.path.join(S.REPO_ROOT, "rigs") + "/",
             "%s:/tmp/toolshed-check/src/rigs/" % HOST],
            check=True, timeout=180)
        proc = subprocess.run(SSH + [HOST, REMOTE], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
        cls.rc = proc.returncode
        cls.out = proc.stdout
        cls.lines = cls.out.splitlines()

    def _writes(self):
        try:
            start = next(i for i, l in enumerate(self.lines)
                         if l.startswith("Writes and library additions"))
        except StopIteration:
            self.fail("no 'Writes and library additions' block in plan output:\n" + self.out)
        block = []
        for line in self.lines[start + 1:]:
            if not line.startswith("  "):
                break
            block.append(line.strip())
        out = []
        for line in block:
            m = re.match(r"([a-z0-9-]+\.[a-z0-9-]+): (\S+)", line)
            if m:
                out.append((m.group(1), m.group(2)))
        return out

    def test_plan_exits_zero_with_status_planned(self):
        self.assertEqual(self.rc, 0, self.out[-3000:])
        status = [l for l in self.lines if l.startswith("Status:")]
        self.assertEqual(status, ["Status: planned"], self.out[-3000:])
        after = self.lines[self.lines.index("Status: planned") + 1:]
        self.assertEqual([l for l in after if l.strip() and not l.startswith("Warning:")], [],
                         "nothing but warnings may follow the status line")

    def test_only_warnings_are_builtin_yolo_one_per_seat(self):
        warnings = [l for l in self.lines if re.match(r"\s*(Warning|Error)\b", l)]
        pat = re.compile(r'Warning: ([a-z0-9-]+\.[a-z0-9-]+): permission_policy ref="builtin:yolo"')
        seats = []
        for w in warnings:
            m = pat.match(w)
            if m is None:
                self.fail("unexpected warning/error: %r" % w)
            seats.append(m.group(1))
        self.assertEqual(sorted(seats), sorted(_seats()))

    def test_skill_written_for_lead_and_builder_seats(self):
        writes = self._writes()
        lead = [d for s, d in writes if s == "orch.lead" and d.endswith("/" + SKILL_ID)]
        build = [d for s, d in writes if s == "dev.build" and d.endswith("/" + SKILL_ID)]
        self.assertEqual(len(lead), 1, writes)
        self.assertIn(".agents/skills/" + SKILL_ID, lead[0])
        self.assertEqual(len(build), 1, writes)
        self.assertIn(".claude/skills/" + SKILL_ID, build[0])

    def test_skill_not_written_for_review_or_qa_seats(self):
        writes = self._writes()
        for seat in ("dev.review", "dev.qa"):
            with self.subTest(seat=seat):
                self.assertTrue([d for s, d in writes if s == seat], "seat %s has no writes" % seat)
                self.assertEqual([d for s, d in writes if s == seat and SKILL_ID in d], [])

    def test_each_seats_skill_writes_match_its_profile(self):
        agent = S.load_yaml(os.path.join(S.AGENT_DIR, "agent.yaml"))
        writes = self._writes()
        for seat, profile in sorted(_seats().items()):
            with self.subTest(seat=seat, profile=profile):
                written = sorted(d.rsplit("/", 1)[1] for s, d in writes
                                 if s == seat and "/skills/" in d)
                self.assertEqual(written, sorted(agent["profiles"][profile]["uses"]["skills"]))

    def test_context_pack_precondition_shown(self):
        self.assertIn(CONTEXT_CMD, self.out)


if __name__ == "__main__":
    unittest.main()
