from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "tools" / "merge_queue.py"
sys.path.insert(0, str(ROOT))
PYTHON = sys.executable


def run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and result.returncode:
        raise AssertionError(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stdout}")
    return result


def git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args], repo).stdout.strip()


def make_repos():
    tmp = tempfile.TemporaryDirectory(prefix="merge-queue-tests-")
    root = Path(tmp.name)
    source = root / "source"
    bare = root / "integration.git"
    source.mkdir()
    run(["git", "init", "-b", "main"], source)
    run(["git", "-C", str(source), "config", "user.name", "Queue Test"], source)
    run(["git", "-C", str(source), "config", "user.email", "queue-test@localhost"], source)
    (source / "base.txt").write_text("base\n", encoding="utf-8")
    run(["git", "-C", str(source), "add", "."], source)
    run(["git", "-C", str(source), "commit", "-m", "base"], source)
    run(["git", "init", "--bare", "-b", "main", str(bare)], root)
    run(["git", "-C", str(bare), "remote", "add", "origin", str(source)], root)
    run(["git", "-C", str(bare), "fetch", "origin"], root)
    git(bare, "update-ref", "refs/heads/main", "refs/remotes/origin/main")
    return tmp, source, bare


class MergeQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.source, self.bare = make_repos()
        self.base = git(self.bare, "rev-parse", "main")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cmd(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return run([PYTHON, str(SCRIPT), "--repo", str(self.bare), *args], self.source, check)

    def branch(self, name: str, filename: str, text: str) -> None:
        git(self.source, "checkout", "-b", name, "main")
        (self.source / filename).write_text(text, encoding="utf-8")
        git(self.source, "add", filename)
        git(self.source, "-c", "user.name=Queue Test", "-c", "user.email=queue-test@localhost", "commit", "-m", name)
        commit = git(self.source, "rev-parse", "HEAD")
        run(["git", "-C", str(self.bare), "fetch", str(self.source), f"{commit}:refs/heads/{name}"], self.source)
        git(self.source, "checkout", "main")

    def test_drain_success_idempotency_and_clean_integration_clone(self) -> None:
        self.branch("feature-one", "feature.txt", "ok\n")
        expected = git(self.bare, "rev-parse", "feature-one")
        self.cmd("enqueue", "feature-one")
        result = self.cmd("drain", "--target", "main", "--upstream", "origin/main", "--test", json.dumps([PYTHON, "-c", "from pathlib import Path; assert Path('feature.txt').read_text() == 'ok\\n'"]))
        self.assertIn("drain complete: processed=1", result.stdout)
        head = git(self.bare, "rev-parse", "main")
        self.assertNotEqual(head, expected)
        self.assertEqual(git(self.bare, "rev-parse", "refs/heads/main^2"), expected)
        self.assertEqual(git(self.bare, "rev-parse", "refs/heads/main^1"), self.base)
        state = json.loads((self.bare / "merge-queue-state.json").read_text())
        self.assertEqual(len(state["completed"]), 1)
        duplicate = self.cmd("enqueue", "feature-one")
        self.assertIn("already queued or integrated", duplicate.stdout)
        self.assertEqual(len(json.loads((self.bare / "merge-queue-state.json").read_text())["pending"]), 0)

    def test_test_failure_conflict_and_stale_candidate_are_rejected(self) -> None:
        self.branch("feature-fail", "failure.txt", "x\n")
        self.cmd("enqueue", "feature-fail")
        failed = self.cmd("drain", "--test", json.dumps([PYTHON, "-c", "raise SystemExit(7)"]))
        self.assertIn("test failed (7)", failed.stdout)
        self.assertEqual(git(self.bare, "rev-parse", "main"), self.base)

        self.branch("feature-conflict", "base.txt", "candidate change\n")
        git(self.source, "checkout", "main")
        (self.source / "base.txt").write_text("target change\n", encoding="utf-8")
        git(self.source, "add", "base.txt")
        git(self.source, "-c", "user.name=Queue Test", "-c", "user.email=queue-test@localhost", "commit", "-m", "advance target with conflicting edit")
        target = git(self.source, "rev-parse", "HEAD")
        run(["git", "-C", str(self.bare), "fetch", "origin", f"{target}:refs/heads/main"], self.source)
        self.cmd("enqueue", "feature-conflict")
        conflict = self.cmd("drain", "--test", json.dumps([PYTHON, "-c", "pass"]))
        self.assertIn("stale base", conflict.stdout)
        self.assertEqual(git(self.bare, "rev-parse", "main"), target)

        self.branch("feature-stale", "stale.txt", "stale\n")
        self.branch("advance-main", "advance.txt", "advance\n")
        advanced = git(self.source, "rev-parse", "advance-main")
        run(["git", "-C", str(self.bare), "update-ref", "refs/heads/main", advanced], self.source)
        self.cmd("enqueue", "feature-stale")
        stale = self.cmd("drain", "--test", json.dumps([PYTHON, "-c", "pass"]))
        self.assertIn("stale base", stale.stdout)
        self.assertEqual(git(self.bare, "rev-parse", "main"), advanced)

    def test_refuses_wrong_upstream_network_origin_and_non_bare_target(self) -> None:
        self.branch("feature-two", "ok.txt", "ok\n")
        self.cmd("enqueue", "feature-two")
        bad = self.cmd("drain", "--upstream", "origin/missing", "--test", json.dumps([PYTHON, "-c", "pass"]), check=False)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("merge queue refused", bad.stdout)
        self.assertEqual(git(self.bare, "rev-parse", "main"), self.base)

        run(["git", "-C", str(self.bare), "remote", "set-url", "origin", "https://example.invalid/repo.git"], self.source)
        network = self.cmd("drain", "--test", json.dumps([PYTHON, "-c", "pass"]), check=False)
        self.assertEqual(network.returncode, 2)
        self.assertIn("local-only origin mirror", network.stdout)
        run(["git", "-C", str(self.bare), "remote", "set-url", "origin", str(self.bare)], self.source)

        normal = self.source
        local_clone = self.bare.parent / "normal-clone"
        run(["git", "clone", "-b", "main", str(self.bare), str(local_clone)], self.source)
        refused = run([PYTHON, str(SCRIPT), "--repo", str(local_clone), "drain", "--test", json.dumps([PYTHON, "-c", "pass"])], self.source, check=False)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("canonical bare repository root", refused.stdout)
        self.assertEqual(git(self.bare, "rev-parse", "main"), self.base)


if __name__ == "__main__":
    unittest.main(verbosity=2)
