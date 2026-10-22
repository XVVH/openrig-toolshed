"""Pin 7: the install preview on the-claw plans cleanly and writes the skill to lead and builder.

Ask, 'Done looks like' 4: `rig bundle install ... --preset recommended --plan`
previews cleanly (no schema errors). OpenRig (`rig` 0.6.14) lives on the-claw;
each run creates its own scratch dir /tmp/toolshed-check-<uuid4 hex> there
(src/, proj/ as a fresh git repo, target/), syncs rigs/ into it, builds the
bundle and runs the read-only --plan install inside it, then removes exactly
that dir. Concurrent runs never share remote state. Nothing outside that dir
on the-claw is touched (never ~/rigs). Skipped when `ssh claw-auto` is not
reachable so the suite stays green offline.
"""
import os
import re
import shlex
import subprocess
import unittest
import uuid

import _support as S

HOST = "claw-auto"
REMOTE_PATH = "export PATH=/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:$PATH; "
RUN_DIR_RE = re.compile(r"^/tmp/toolshed-check-[0-9a-f]{32}$")
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


def _run_dir():
    """A fresh remote scratch path, unique to this run."""
    return "/tmp/toolshed-check-" + uuid.uuid4().hex


def _prepare_cmd(d):
    """Create the run dir (fails if it already exists) with src/, proj/ (git repo), target/."""
    q = shlex.quote
    return (REMOTE_PATH + "mkdir %s && mkdir %s %s %s && git init -q %s"
            % (q(d), q(d + "/src"), q(d + "/proj"), q(d + "/target"), q(d + "/proj")))


def _plan_cmd(d):
    """Build the bundle into d and run the --plan install in d/proj against d/target."""
    q = shlex.quote
    bundle = d + "/toolshed.rigbundle"
    return (REMOTE_PATH +
            "cd %s && " % q(d + "/src") +
            "rig bundle create rigs/toolshed/rig.yaml --preset recommended "
            "--min-cli-version 0.6.6 --min-daemon-version 0.6.6 -o %s && " % q(bundle) +
            "cd %s && " % q(d + "/proj") +
            "rig bundle install %s --target %s --cwd . --plan" % (q(bundle), q(d + "/target")))


def _remove_run_dir(d):
    """rm -rf exactly this run's dir; refuse anything that is not a per-run path."""
    if not RUN_DIR_RE.match(d):
        raise ValueError("refusing to remove %r: not a per-run scratch dir" % d)
    subprocess.run(SSH + [HOST, "rm -rf -- %s" % shlex.quote(d)], check=True, timeout=120)


@unittest.skipUnless(_reachable(), "ssh %s unreachable; install preview not run" % HOST)
class InstallPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Chosen before anything runs remotely so cleanup always knows the exact path.
        cls.remote_dir = _run_dir()
        try:
            subprocess.run(SSH + [HOST, _prepare_cmd(cls.remote_dir)], check=True, timeout=120)
            subprocess.run(
                ["rsync", "-a", "--delete", "--exclude", ".git",
                 os.path.join(S.REPO_ROOT, "rigs") + "/",
                 "%s:%s/src/rigs/" % (HOST, cls.remote_dir)],
                check=True, timeout=180)
            proc = subprocess.run(SSH + [HOST, _plan_cmd(cls.remote_dir)],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  universal_newlines=True, timeout=600)
        except BaseException:
            # unittest skips tearDownClass when setUpClass raises; clean up here instead,
            # without letting a cleanup error mask the original one.
            try:
                cls.tearDownClass()
            except Exception:
                pass
            raise
        cls.rc = proc.returncode
        cls.out = proc.stdout
        cls.lines = cls.out.splitlines()

    @classmethod
    def tearDownClass(cls):
        _remove_run_dir(cls.remote_dir)

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
