"""Reject private source/runtime paths and recognizable secret formats in Git's tracked tree."""

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    rb"\bAKIA[A-Z0-9]{16}\b",
    rb"\bghp_[A-Za-z0-9]{30,}\b",
    rb"\bgithub_pat_[A-Za-z0-9_]{30,}\b",
    rb"\bsk-proj-[A-Za-z0-9_-]{30,}\b",
]


def forbidden(name):
    parts = Path(name).parts
    return (
        any(p in {".local", ".venv", "node_modules", "contexto", "__pycache__"} for p in parts)
        or name.startswith("data/private/")
        or (Path(name).name.startswith(".env") and name != ".env.example")
        or Path(name).suffix.lower() in {".pdf", ".zip", ".db", ".log", ".pyc", ".bundle"}
        or (
            name.startswith("data/")
            and name not in {"data/README.md", "data/demo/sales.csv", "data/demo/master.json"}
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true", help="Also inspect every reachable commit")
    args = parser.parse_args()
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    violations = []
    count = 0
    if not any(tracked):
        raise SystemExit("No tracked files: stage the intended public tree before running this check")
    for name in filter(None, tracked):
        path = ROOT / name
        if forbidden(name):
            violations.append((name, "private/source/runtime path"))
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raw = path.read_bytes()
            if any(re.search(pattern, raw) for pattern in PATTERNS):
                violations.append((name, "recognizable credential/private-key pattern"))
        count += 1
    if args.history:
        commits = subprocess.check_output(["git", "rev-list", "--all"], cwd=ROOT).decode().splitlines()
        seen = set()
        for commit in commits:
            tree = subprocess.check_output(["git", "ls-tree", "-rz", commit], cwd=ROOT)
            for entry in filter(None, tree.split(b"\0")):
                metadata, raw_name = entry.split(b"\t", 1)
                name = raw_name.decode("utf-8")
                oid = metadata.split()[2].decode()
                if forbidden(name):
                    violations.append((name, "forbidden path in history"))
                if oid not in seen and Path(name).suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                    raw = subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)
                    if any(re.search(pattern, raw) for pattern in PATTERNS):
                        violations.append((name, "recognizable secret in history"))
                seen.add(oid)
        print(f"Inspected {len(commits)} reachable commits and {len(seen)} unique historical blobs.")
    if violations:
        for name, reason in violations:
            print(f"FAIL {name}: {reason}")
        raise SystemExit(1)
    print(f"PASS: {count} tracked files checked; no forbidden paths or recognizable secret patterns.")


if __name__ == "__main__":
    main()
