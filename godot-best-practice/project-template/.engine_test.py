#!/usr/bin/env python3
"""用项目里的 .engine.bat / .engine.sh 导出 debug 包并跑一个测试。

一次只跑一个：

  python .engine_test.py
  python .engine_test.py --smoke

先把 debug 包导出到临时目录下的 GUID 子目录，然后用该包跑 TESTS 里对应的 GDScript。stdout / stderr 原样打出。
出现错误或警告立刻结束本次拉起的进程。时间上限写在 GDScript 入口里，不在这里。
Autoload tests/test_entry.gd 读取 --test=res://....gd，load 后 new() 挂到自己下面。测试不使用 tscn。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ENGINE = PROJECT / (".engine.bat" if sys.platform == "win32" else ".engine.sh")
EXPORT_PRESET = "Windows Desktop Test" if sys.platform == "win32" else "Linux Desktop Test"

TESTS: dict[str, str] = {
    "smoke": "res://tests/smoke.gd",
}

OFFENDING_PREFIXES = (
    "SCRIPT ERROR:",
    "ERROR:",
    "WARNING:",
    "USER WARNING:",
    "USER ERROR:",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="导出 debug 包并跑一个测试")
    for name in TESTS:
        parser.add_argument(f"--{name}", action="store_true", help=TESTS[name])
    args = parser.parse_args(argv)
    selected = [name for name in TESTS if getattr(args, name)]
    if not selected:
        selected = ["smoke"]
    if len(selected) != 1:
        names = " ".join(f"--{name}" for name in TESTS)
        print(f"一次只能跑一个测试，可选：{names}", file=sys.stderr)
        return 2
    test_name = selected[0]
    with tempfile.TemporaryDirectory(prefix="godot-test-") as export_dir:
        binary = export_debug(Path(export_dir))
        if binary is None:
            return 1
        return run_and_watch(launch_command(binary, TESTS[test_name]))


def export_debug(export_dir: Path) -> Path | None:
    output_dir = export_dir / str(uuid.uuid4())
    output_dir.mkdir(parents=True)
    output = output_dir / ("game.exe" if sys.platform == "win32" else "game")
    command = engine_command(
        "--headless",
        "--path",
        str(PROJECT),
        "--export-debug",
        EXPORT_PRESET,
        str(output),
    )
    if run_and_watch(command) != 0:
        return None
    binary = exported_binary(output)
    if binary is None:
        print(f"导出产物不存在：{output}", file=sys.stderr)
        return None
    return binary


def exported_binary(output: Path) -> Path | None:
    if sys.platform == "win32":
        console = output.with_name(output.stem + ".console.exe")
        if console.is_file():
            return console
    if output.is_file():
        return output
    return None


def engine_command(*arguments: str) -> list[str]:
    if ENGINE.suffix.lower() == ".bat":
        return ["cmd", "/c", str(ENGINE), *arguments]
    return [str(ENGINE), *arguments]


def launch_command(binary: Path, scene: str) -> list[str]:
    return [str(binary), "--", f"--test={scene}"]


def run_and_watch(command: list[str]) -> int:
    process = subprocess.Popen(
        command,
        cwd=PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None
    offending = False
    for raw_line in process.stdout:
        sys.stdout.write(raw_line)
        sys.stdout.flush()
        line = raw_line.strip()
        if any(line.startswith(prefix) for prefix in OFFENDING_PREFIXES):
            offending = True
            stop(process)
            print(f"日志出现错误或警告，已停止：{line}", file=sys.stderr)
            break
    return_code = process.wait()
    if offending:
        return 1
    return return_code


def stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            text=True,
        )
    else:
        process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
