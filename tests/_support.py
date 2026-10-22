"""Shared helpers for the toolshed lock tests.

The upstream reference is openrig-world at commit 47388ef (rigs/workshop), the
fork point named in the ask. It is never vendored into this repo: it is read
from $OPENRIG_WORLD_SRC, else /tmp/openrig-world-src, else cloned into a cache
directory under tempfile.gettempdir().
"""
import functools
import os
import re
import subprocess
import tempfile

import yaml

UPSTREAM_COMMIT = "47388ef"
UPSTREAM_URL = "https://github.com/mvschwarz/openrig-world"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLSHED = os.path.join(REPO_ROOT, "rigs", "toolshed")
AGENT_DIR = os.path.join(TOOLSHED, "agents", "toolshed")
SKILL_REL = "agents/toolshed/bundle-skills/prototype-before-ask/SKILL.md"

# Finder litter, never part of a bundle (also gitignored here).
IGNORED_NAMES = {".DS_Store"}


def _git(args, cwd=None):
    return subprocess.run(
        ["git"] + args, cwd=cwd, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
    ).stdout.strip()


@functools.lru_cache(maxsize=None)
def upstream_root():
    """Path to a checkout of openrig-world at 47388ef. Fails loudly otherwise."""
    candidates = []
    env = os.environ.get("OPENRIG_WORLD_SRC")
    if env:
        candidates.append(env)
    candidates.append("/tmp/openrig-world-src")
    src = next((c for c in candidates if os.path.isdir(c)), None)
    if src is None:
        src = os.path.join(tempfile.gettempdir(), "openrig-world-%s" % UPSTREAM_COMMIT)
        if not os.path.isdir(os.path.join(src, ".git")):
            _git(["clone", "--filter=blob:none", UPSTREAM_URL, src])
        _git(["checkout", "-q", UPSTREAM_COMMIT], cwd=src)
    try:
        head = _git(["rev-parse", "HEAD"], cwd=src)
    except (subprocess.CalledProcessError, OSError) as exc:
        raise AssertionError("upstream reference %s is not a git checkout: %s" % (src, exc))
    if not head.startswith(UPSTREAM_COMMIT):
        raise AssertionError(
            "upstream reference %s is at %s, not the fork point %s"
            % (src, head, UPSTREAM_COMMIT))
    workshop = os.path.join(src, "rigs", "workshop")
    if not os.path.isdir(workshop):
        raise AssertionError("no rigs/workshop under upstream reference %s" % src)
    return workshop


def upstream_path(rel_toolshed):
    """Upstream counterpart of a path relative to rigs/toolshed."""
    rel = rel_toolshed
    if rel.startswith("agents/toolshed/") or rel == "agents/toolshed":
        rel = "agents/workshop" + rel[len("agents/toolshed"):]
    return os.path.join(upstream_root(), rel)


def file_tree(root):
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            if name in IGNORED_NAMES:
                continue
            full = os.path.join(dirpath, name)
            out.add(os.path.relpath(full, root).replace(os.sep, "/"))
    return out


def rename(text):
    return text.replace("workshop", "toolshed").replace("Workshop", "Toolshed")


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def norm(text):
    """Lowercase, drop markdown emphasis/backticks, collapse whitespace."""
    text = text.replace("`", "").replace("*", "")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", text).strip().lower()


def sentences(text):
    """Split normalised text into rough sentences."""
    return [s for s in re.split(r"(?<=[.!?;:])\s+|\s+-\s+(?=[a-z])", text) if s]
