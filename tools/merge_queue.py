#!/usr/bin/env python3
"""Local, fail-closed Git merge queue prototype; never pushes to a remote."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def git(repo: Path, *args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed ({result.returncode})")
    return result


def git_dir(repo: Path) -> Path:
    value = git(repo, "rev-parse", "--absolute-git-dir").stdout.strip()
    path = Path(value)
    if not path.is_absolute():
        raise RuntimeError("Git returned a non-absolute common directory")
    return path.resolve()


@contextlib.contextmanager
def file_lock(path: Path, blocking: bool = True):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    unlock = None
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if not handle.read(1):
                handle.seek(0)
                handle.write(b"0")
                handle.flush()
            while True:
                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if not blocking:
                        raise RuntimeError(f"queue lock is busy: {path.name}") from exc
                    time.sleep(0.1)

            def unlock() -> None:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
            try:
                fcntl.flock(handle.fileno(), flags)
            except BlockingIOError as exc:
                raise RuntimeError(f"queue lock is busy: {path.name}") from exc

            def unlock() -> None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        try:
            yield
        finally:
            unlock()
    finally:
        handle.close()


def state_paths(repo: Path) -> tuple[Path, Path, Path]:
    root = git_dir(repo)
    return root / "merge-queue-state.json", root / "merge-queue-state.lock", root / "merge-queue-worker.lock"


def read_state(path: Path) -> dict:
    if not path.exists():
        return {"pending": [], "completed": [], "rejected": []}
    state = json.loads(path.read_text(encoding="utf-8"))
    if set(state) != {"pending", "completed", "rejected"} or not all(isinstance(state[k], list) for k in state):
        raise RuntimeError("invalid queue state; refusing to continue")
    return state


def write_state(path: Path, state: dict) -> None:
    fd, name = tempfile.mkstemp(prefix="merge-queue-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def resolve_branch(repo: Path, branch: str) -> str:
    if git(repo, "check-ref-format", "--branch", branch, check=False).returncode:
        raise RuntimeError(f"invalid local branch name: {branch}")
    result = git(repo, "rev-parse", "--verify", f"refs/heads/{branch}^{{commit}}", check=False)
    if result.returncode:
        raise RuntimeError(f"local branch does not exist: {branch}")
    return result.stdout.strip()


def enqueue(repo: Path, branch: str) -> str:
    commit = resolve_branch(repo, branch)
    queue_file, state_lock, _ = state_paths(repo)
    with file_lock(state_lock):
        state = read_state(queue_file)
        if any(item["commit"] == commit for item in state["pending"] + state["completed"]):
            return f"already queued or integrated: {branch} {commit[:12]}"
        state["pending"].append({"branch": branch, "commit": commit, "queued_at": int(time.time())})
        write_state(queue_file, state)
    return f"queued: {branch} {commit[:12]}"


def checked_out_branches(repo: Path) -> set[str]:
    result = git(repo, "worktree", "list", "--porcelain", check=False)
    return {line.removeprefix("branch refs/heads/") for line in result.stdout.splitlines() if line.startswith("branch refs/heads/")}


def run_one(repo: Path, target: str, item: dict, tests: list[str]) -> tuple[bool, str]:
    target_ref = f"refs/heads/{target}"
    base = git(repo, "rev-parse", "--verify", f"{target_ref}^{{commit}}", check=False)
    if base.returncode:
        return False, f"target branch does not exist: {target}"
    target_sha = base.stdout.strip()
    candidate = item["commit"]
    current = git(repo, "rev-parse", "--verify", f"refs/heads/{item['branch']}^{{commit}}", check=False)
    if current.returncode or current.stdout.strip() != candidate:
        return False, f"candidate branch moved or disappeared: {item['branch']}"
    if git(repo, "merge-base", "--is-ancestor", candidate, target_sha, check=False).returncode == 0:
        return True, f"already integrated: {item['branch']} {candidate[:12]}"
    if git(repo, "merge-base", "--is-ancestor", target_sha, candidate, check=False).returncode:
        return False, f"stale base: {item['branch']} does not contain current {target}"
    if target in checked_out_branches(repo):
        return False, f"target branch is checked out in this repository; use a dedicated bare integration clone"

    worktree = Path(tempfile.mkdtemp(prefix="merge-queue-"))
    worktree.rmdir()
    added = git(repo, "worktree", "add", "--detach", str(worktree), target_sha, check=False)
    if added.returncode:
        return False, f"cannot create integration worktree: {added.stderr.strip()}"
    try:
        merged = git(worktree, "-c", "user.name=Local Merge Queue", "-c", "user.email=merge-queue@localhost", "merge", "--no-commit", "--no-ff", "-m", f"Merge {item['branch']} into {target}", candidate, check=False)
        if merged.returncode:
            git(worktree, "merge", "--abort", check=False)
            return False, f"merge conflict or merge error: {merged.stderr.strip() or merged.stdout.strip()}"
        for arg in tests:
            result = subprocess.run(arg, cwd=worktree, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                return False, f"test failed ({result.returncode}): {' '.join(arg)}\n{result.stdout[-4000:]}"
        if git(worktree, "diff", "--quiet", check=False).returncode:
            return False, "tests modified tracked files; refusing merge"
        if git(worktree, "ls-files", "--others", "--exclude-standard").stdout.strip():
            return False, "tests left untracked files; refusing merge"
        git(worktree, "-c", "user.name=Local Merge Queue", "-c", "user.email=merge-queue@localhost", "commit", "-m", f"Merge {item['branch']} into {target}")
        merge_sha = git(worktree, "rev-parse", "HEAD").stdout.strip()
        first_parent = git(worktree, "rev-parse", "HEAD^1").stdout.strip()
        if first_parent != target_sha:
            return False, "merge commit first parent changed; refusing target update"
        updated = git(repo, "update-ref", target_ref, merge_sha, target_sha, check=False)
        if updated.returncode:
            return False, f"target changed concurrently; compare-and-swap refused: {updated.stderr.strip()}"
        return True, f"merged: {item['branch']} {candidate[:12]} -> {merge_sha[:12]}"
    finally:
        removed = git(repo, "worktree", "remove", str(worktree), check=False)
        if removed.returncode:
            # Preserve evidence rather than force-removing a dirty worktree.
            print(f"warning: temporary worktree retained at {worktree}: {removed.stderr.strip()}", file=sys.stderr)


def drain(repo: Path, target: str, tests: list[list[str]], upstream: str | None) -> int:
    if not tests:
        raise RuntimeError("at least one real test command is required via --test")
    for command in tests:
        if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
            raise RuntimeError("test commands must be non-empty argv arrays")
    root = git_dir(repo)
    if repo.resolve() != root.resolve():
        raise RuntimeError("run drain from the canonical bare repository root, not an attached worktree")
    if git(repo, "rev-parse", "--is-bare-repository").stdout.strip() != "true":
        raise RuntimeError("run drain from a dedicated bare integration clone; this prototype never updates a checked-out branch")
    remote = git(repo, "remote", "get-url", "origin", check=False)
    if not remote.returncode:
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s]+|[^\s]+@[^\s]+:[^\s]+", remote.stdout.strip()):
            raise RuntimeError("origin is a network remote; use a local-only origin mirror")
    queue_file, state_lock, worker_lock = state_paths(repo)
    processed = 0
    with file_lock(worker_lock):
        if upstream:
            target_sha = git(repo, "rev-parse", "--verify", f"refs/heads/{target}^{{commit}}").stdout.strip()
            upstream_sha = git(repo, "rev-parse", "--verify", f"refs/remotes/{upstream}^{{commit}}").stdout.strip()
            if target_sha != upstream_sha:
                raise RuntimeError(f"target {target} differs from {upstream}; fetch/align explicitly before draining")
        while True:
            with file_lock(state_lock):
                state = read_state(queue_file)
                if not state["pending"]:
                    break
                item = state["pending"][0]
            ok, message = run_one(repo, target, item, tests)
            with file_lock(state_lock):
                state = read_state(queue_file)
                if not state["pending"] or state["pending"][0] != item:
                    raise RuntimeError("queue head changed unexpectedly; refusing to continue")
                state["pending"].pop(0)
                record = {**item, "result": message, "finished_at": int(time.time())}
                state["completed" if ok else "rejected"].append(record)
                write_state(queue_file, state)
            print(message)
            processed += 1
    print(f"drain complete: processed={processed}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="bare Git integration clone")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("enqueue", help="snapshot a local candidate branch into the queue")
    add.add_argument("branch")
    worker = sub.add_parser("drain", help="serially test and integrate queued candidates")
    worker.add_argument("--target", default="main")
    worker.add_argument("--upstream", help="require target to match refs/remotes/<upstream> before processing")
    worker.add_argument("--test", action="append", required=True, help="test argv as a JSON string array; repeat for more commands")
    sub.add_parser("status", help="show queue state")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    try:
        if args.command == "enqueue":
            print(enqueue(repo, args.branch))
        elif args.command == "drain":
            commands = [json.loads(raw) for raw in args.test]
            if not all(isinstance(command, list) and command and all(isinstance(part, str) for part in command) for command in commands):
                raise RuntimeError("each --test must be a JSON array of non-empty strings")
            return drain(repo, args.target, commands, args.upstream)
        else:
            queue_file, state_lock, _ = state_paths(repo)
            with file_lock(state_lock):
                print(json.dumps(read_state(queue_file), indent=2, sort_keys=True))
        return 0
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"merge queue refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
