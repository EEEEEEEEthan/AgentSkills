"""Recap-video helper: check that every issue number touched in a period is named in the showreel.

Collects `#<n>` tokens from `git log --since` and looks each one up in narration.json and
timeline.json (captions, narration text, chapter issue lists). Exit code 1 prints exactly
which numbers are missing.

Usage (from the repository root):
    python3 <WORK_DIR>/check_coverage.py [--since "2026-11-11 00:00"] [--dir <WORK_DIR>]

(Windows: `py -3`.) The defaults cover "everything committed today" in `--dir .export/showreel`;
change that default (or pass `--dir`) to your own `<WORK_DIR>`.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ISSUE_PATTERN = re.compile(r"#\d+")


def git_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise SystemExit(f"找不到 git 仓库根：{start}")


def day_issues(repo_root: Path, since: str) -> list[str]:
    log = subprocess.run(
        ["git", "log", f"--since={since}", "--pretty=%s"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout
    seen: list[str] = []
    for number in ISSUE_PATTERN.findall(log):
        if number not in seen:
            seen.append(number)
    return seen


def showreel_text(directory: Path) -> str:
    parts = []
    for name in ("narration.json", "timeline.json"):
        path = directory / name
        if not path.exists():
            raise SystemExit(f"缺少 {path}")
        parts.append(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False))
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".export/showreel")
    parser.add_argument(
        "--since",
        default=datetime.date.today().strftime("%Y-%m-%d 00:00"),
        help="git log --since，默认今天 00:00",
    )
    arguments = parser.parse_args()
    directory = Path(arguments.dir).resolve()
    repo_root = git_root(directory)
    issues = day_issues(repo_root, arguments.since)
    text = showreel_text(directory)
    missing = [issue for issue in issues if issue not in text]
    for issue in missing:
        print(f"MISSING {issue}")
    if missing:
        print(f"coverage failed {len(issues) - len(missing)}/{len(issues)}")
        return 1
    print(f"coverage ok {len(issues)}/{len(issues)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
