"""Pin 5: the skill is registered and selected by lead and builder only.

Ask, 'What it is' 1 and 4, Constraints: the skill lands on both the lead and the
builder profiles; Workshop's structure, permissions (builtin:yolo) and edges are
otherwise untouched.
"""
import copy
import os
import unittest

import _support as S

SKILL_ID = "prototype-before-ask"
SKILL_ENTRY = {"id": SKILL_ID, "path": "bundle-skills/prototype-before-ask"}
SELECTS = ("lead", "builder")
DOES_NOT = ("code-reviewer", "qa")


def _agents():
    up = S.load_yaml(S.upstream_path("agents/toolshed/agent.yaml"))
    ours = S.load_yaml(os.path.join(S.AGENT_DIR, "agent.yaml"))
    return up, ours


def _rigs():
    return (S.load_yaml(S.upstream_path("rig.yaml")),
            S.load_yaml(os.path.join(S.TOOLSHED, "rig.yaml")))


class AgentYaml(unittest.TestCase):
    def test_skill_resource_registered_and_present_on_disk(self):
        _, ours = _agents()
        entries = [s for s in ours["resources"]["skills"] if s.get("id") == SKILL_ID]
        self.assertEqual(entries, [SKILL_ENTRY])
        self.assertTrue(os.path.isfile(os.path.join(S.AGENT_DIR, SKILL_ENTRY["path"], "SKILL.md")))

    def test_skill_resources_are_upstreams_plus_the_one_entry(self):
        up, ours = _agents()
        rest = [s for s in ours["resources"]["skills"] if s.get("id") != SKILL_ID]
        self.assertEqual(rest, up["resources"]["skills"])
        self.assertEqual(len(ours["resources"]["skills"]), len(up["resources"]["skills"]) + 1)

    def test_other_resources_unchanged(self):
        up, ours = _agents()
        for key in sorted(set(up["resources"]) | set(ours["resources"])):
            if key == "skills":
                continue
            with self.subTest(resource=key):
                self.assertEqual(ours["resources"].get(key), up["resources"].get(key))

    def test_profile_set_unchanged(self):
        up, ours = _agents()
        self.assertEqual(sorted(ours["profiles"]), sorted(up["profiles"]))

    def test_lead_and_builder_select_the_skill(self):
        up, ours = _agents()
        for name in SELECTS:
            with self.subTest(profile=name):
                skills = ours["profiles"][name]["uses"]["skills"]
                self.assertIn(SKILL_ID, skills)
                self.assertEqual(sorted(set(skills) - {SKILL_ID}),
                                 sorted(up["profiles"][name]["uses"]["skills"]),
                                 "lead/builder keep upstream's skills plus prototype-before-ask")

    def test_code_reviewer_and_qa_do_not_select_the_skill(self):
        up, ours = _agents()
        for name in DOES_NOT:
            with self.subTest(profile=name):
                skills = ours["profiles"][name]["uses"]["skills"]
                self.assertNotIn(SKILL_ID, skills)
                self.assertEqual(skills, up["profiles"][name]["uses"]["skills"])

    def test_every_profile_keeps_plugins_runtime_resources_and_startup(self):
        up, ours = _agents()
        for name, prof in sorted(up["profiles"].items()):
            mine = ours["profiles"][name]
            for key in ("plugins", "runtime_resources"):
                with self.subTest(profile=name, uses=key):
                    self.assertEqual(mine.get("uses", {}).get(key), prof.get("uses", {}).get(key))
            with self.subTest(profile=name, field="startup"):
                self.assertEqual(mine.get("startup"), prof.get("startup"))
            with self.subTest(profile=name, field="preferences"):
                self.assertEqual(mine.get("preferences"), prof.get("preferences"))


def _strip_agent_ref(pods):
    pods = copy.deepcopy(pods)
    for pod in pods:
        for m in pod.get("members", []):
            m.pop("agent_ref", None)
    return pods


class RigYaml(unittest.TestCase):
    def test_every_member_uses_the_toolshed_agent(self):
        _, ours = _rigs()
        refs = [m.get("agent_ref") for p in ours["pods"] for m in p.get("members", [])]
        self.assertTrue(refs)
        self.assertEqual(set(refs), {"local:agents/toolshed"})
        self.assertTrue(os.path.isfile(os.path.join(S.TOOLSHED, "agents", "toolshed", "agent.yaml")))

    def test_pods_edges_and_permissions_unchanged(self):
        up, ours = _rigs()
        self.assertEqual(_strip_agent_ref(ours["pods"]), _strip_agent_ref(up["pods"]))
        self.assertEqual(ours.get("edges"), up.get("edges"))
        self.assertEqual(ours.get("permission_policy"), up.get("permission_policy"))
        self.assertEqual(ours.get("permission_policy"), "builtin:yolo")
        self.assertEqual(ours.get("non_interruptive"), up.get("non_interruptive"))


if __name__ == "__main__":
    unittest.main()
