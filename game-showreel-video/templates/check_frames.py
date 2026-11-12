"""Check that no shot of the showreel is a blank or nearly-blank picture.

Every recorded frame is a JPEG, so its byte size is a cheap proxy for how much detail
the picture carries. Per shot we require a median of at least 30 KB, and nowhere a run
of five consecutive frames under 12 KB (that is a black card or a stalled renderer).
"""

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "frames"
MEDIAN_MINIMUM_BYTES = 30_000
FLOOR_BYTES = 12_000
BLANK_RUN_LIMIT = 5


def main() -> int:
    timeline = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
    failed = False
    for chapter in timeline["chapters"]:
        for shot in chapter["shots"]:
            sizes = []
            for index in range(shot["start_frame"], shot["start_frame"] + shot["frames"]):
                path = FRAMES / f"{index:06d}.jpg"
                if not path.exists():
                    print(f"MISSING frame {path}")
                    failed = True
                    break
                sizes.append(path.stat().st_size)
            if not sizes:
                continue
            median = int(statistics.median(sizes))
            run = 0
            worst_run = 0
            for size in sizes:
                run = run + 1 if size < FLOOR_BYTES else 0
                worst_run = max(worst_run, run)
            verdict = "ok" if median >= MEDIAN_MINIMUM_BYTES and worst_run < BLANK_RUN_LIMIT else "FAIL"
            if verdict == "FAIL":
                failed = True
            print(
                f"{verdict:<4} {shot['id']:<16} median={median // 1024:>4}KB "
                f"longest_blank_run={worst_run} frames={len(sizes)}"
            )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
