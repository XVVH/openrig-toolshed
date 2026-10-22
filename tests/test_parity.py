"""Pins 1, 2 and 6: rigs/toolshed is upstream rigs/workshop, renamed, plus one skill.

Ask, 'Done looks like' 1 and 3: same file tree, renamed; the diff against the
forked workshop tree shows only the new skill, the renamed metadata and one
inserted paragraph each in lead.md and builder.md -- nothing else touched.
"""
import os
import re
import unittest

import _support as S

ADDED = {S.SKILL_REL}

# Files allowed to differ from upstream at all. Everything else is byte-identical.
MAY_DIFFER = {
    "README.md",
    "rig.yaml",
    "configurations.yaml",
    "agents/toolshed/agent.yaml",
    "agents/toolshed/guidance/lead.md",
    "agents/toolshed/guidance/builder.md",
}

# Of those, files whose only permitted change is the workshop -> toolshed rename.
RENAME_ONLY = {"rig.yaml", "configurations.yaml"}


def _renamed_upstream_tree():
    out = set()
    for rel in S.file_tree(S.upstream_root()):
        if rel.startswith("agents/workshop/"):
            rel = "agents/toolshed/" + rel[len("agents/workshop/"):]
        out.add(rel)
    return out


class TreeParity(unittest.TestCase):
    def test_upstream_has_no_agents_toolshed_already(self):
        # Guard for the rename mapping below: upstream must only know agents/workshop.
        upstream = S.file_tree(S.upstream_root())
        self.assertFalse([p for p in upstream if p.startswith("agents/toolshed/")])
        self.assertTrue([p for p in upstream if p.startswith("agents/workshop/")])

    def test_tree_is_upstream_renamed_plus_only_the_skill(self):
        expected = _renamed_upstream_tree()
        actual = S.file_tree(S.TOOLSHED)
        added = sorted(actual - expected)
        removed = sorted(expected - actual)
        self.assertEqual(removed, [], "files from upstream rigs/workshop missing in rigs/toolshed")
        self.assertEqual(added, sorted(ADDED),
                         "rigs/toolshed must add exactly the prototype-before-ask SKILL.md")

    def test_no_workshop_agent_dir_left(self):
        self.assertFalse(os.path.exists(os.path.join(S.TOOLSHED, "agents", "workshop")))


class ContentParity(unittest.TestCase):
    def test_every_other_file_is_byte_identical_to_upstream(self):
        changed = []
        for rel in sorted(S.file_tree(S.TOOLSHED) - ADDED - MAY_DIFFER):
            up = S.upstream_path(rel)
            if not os.path.isfile(up):
                continue  # tree test reports this
            if S.read_bytes(up) != S.read_bytes(os.path.join(S.TOOLSHED, rel)):
                changed.append(rel)
        self.assertEqual(changed, [],
                         "files outside the ask's change set differ from upstream 47388ef")

    def test_rig_and_configurations_differ_only_by_the_rename(self):
        for rel in sorted(RENAME_ONLY):
            with self.subTest(file=rel):
                up = S.read_text(S.upstream_path(rel))
                ours = S.read_text(os.path.join(S.TOOLSHED, rel))
                self.assertNotEqual(up, ours, "%s was expected to carry the rename" % rel)
                self.assertEqual(S.rename(up), ours,
                                 "%s differs from upstream by more than workshop->toolshed" % rel)

    def test_rig_yaml_names_the_rig_toolshed(self):
        self.assertEqual(S.load_yaml(os.path.join(S.TOOLSHED, "rig.yaml"))["name"], "toolshed")

    def test_culture_and_startup_untouched(self):
        rels = ["CULTURE.md"] + sorted(
            r for r in S.file_tree(S.TOOLSHED) if r.startswith("startup/"))
        self.assertGreater(len(rels), 1)
        for rel in rels:
            with self.subTest(file=rel):
                self.assertEqual(S.read_bytes(S.upstream_path(rel)),
                                 S.read_bytes(os.path.join(S.TOOLSHED, rel)))


STALE = ("openrig-world/tree/main/rigs/toolshed", "openrig-world/rigs/toolshed")
INSTALL_URL = "https://github.com/XVVH/openrig-toolshed/tree/main/rigs/toolshed"
CONTEXT_CMD = "rig context add --git https://github.com/mvschwarz/openrig-world"


def _text_files():
    files = [os.path.join(S.REPO_ROOT, "README.md")]
    files += [os.path.join(S.TOOLSHED, r) for r in sorted(S.file_tree(S.TOOLSHED))]
    for path in files:
        try:
            yield path, S.read_text(path)
        except UnicodeDecodeError:
            continue


class InstallLinks(unittest.TestCase):
    def test_no_stale_openrig_world_toolshed_links(self):
        hits = []
        for path, text in _text_files():
            for needle in STALE:
                if needle in text:
                    hits.append("%s: %s" % (os.path.relpath(path, S.REPO_ROOT), needle))
        self.assertEqual(hits, [], "toolshed is installed from XVVH/openrig-toolshed")

    def test_every_documented_github_install_points_at_this_repo(self):
        pat = re.compile(r"rig bundle install (https?://\S+)")
        urls = []
        for path, text in _text_files():
            for m in pat.finditer(text):
                urls.append((os.path.relpath(path, S.REPO_ROOT), m.group(1)))
        self.assertTrue(urls, "README should document the GitHub install command")
        bad = [u for u in urls if u[1] != INSTALL_URL]
        self.assertEqual(bad, [])

    def test_context_pack_precondition_still_points_at_openrig_world(self):
        # rig reads preconditions from bundle.yaml; the install plan shows them as
        # "Author setup commands". The openrig-world context pack is correct and stays.
        bundle = S.load_yaml(os.path.join(S.TOOLSHED, "bundle.yaml"))
        commands = [c for p in bundle.get("preconditions", []) for c in (p.get("commands") or [])]
        self.assertIn(CONTEXT_CMD, commands)


if __name__ == "__main__":
    unittest.main()
