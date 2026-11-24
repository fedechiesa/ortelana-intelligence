"""Reject private source/runtime paths and recognizable secret formats in Git's tracked tree."""

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


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    violations = []
    count = 0
    if not any(tracked):
        raise SystemExit("No tracked files: stage the intended public tree before running this check")
    for name in filter(None, tracked):
        parts = Path(name).parts
        if any(p in {".local", ".venv", "node_modules", "contexto", "__pycache__"} for p in parts):
            violations.append((name, "private/runtime directory"))
        if name.startswith("data/private/") or (
            Path(name).name.startswith(".env") and name != ".env.example"
        ):
            violations.append((name, "private data or environment"))
        path = ROOT / name
        if path.suffix.lower() in {".pdf", ".zip", ".db", ".log", ".pyc"}:
            violations.append((name, "source/runtime artifact"))
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raw = path.read_bytes()
            if any(re.search(pattern, raw) for pattern in PATTERNS):
                violations.append((name, "recognizable credential/private-key pattern"))
        count += 1
    if violations:
        for name, reason in violations:
            print(f"FAIL {name}: {reason}")
        raise SystemExit(1)
    print(f"PASS: {count} tracked files checked; no forbidden paths or recognizable secret patterns.")


if __name__ == "__main__":
    main()
