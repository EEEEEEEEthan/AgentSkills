#!/usr/bin/env python3
"""启动 Godot 自动化测试。拷进项目后改 GODOT、EXPORT_PRESET 和 TESTS。

一次只跑一个：

  python test_runner.py --smoke
  python test_runner.py --monkey

先导入资源，再把 debug 包导出到临时目录下的 GUID 子目录，然后用该包跑 TESTS 里对应的 GDScript。stdout / stderr 原样打出。
出现错误或警告立刻结束本次拉起的进程。时间上限写在 GDScript 入口里，不在这里。
游戏入口读取 --test=res://....gd，load 后 new() 挂到根节点。测试不使用 tscn。导出包不接受编辑器的场景路径参数。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# 项目内引擎启动脚本，或 godot 可执行文件。
GODOT = "godot"
# 与 export_presets.cfg 里的预设名一致。
EXPORT_PRESET = "Windows Desktop"
# 含 project.godot 的目录。
PROJECT = Path(".")

# 选项名 -> 脚本。冒烟只有 smoke。其余每一项是一条专项。不要写成 tscn。
TESTS: dict[str, str] = {
    "smoke": "res://tests/smoke/smoke.gd",
    "monkey": "res://tests/special/monkey.gd",
}

# Godot 把脚本错误、引擎错误和警告打成这几种开头。
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
    imported = run_and_watch(
        [GODOT, "--headless", "--path", str(PROJECT), "--import"]
    )
    if imported != 0:
        return None
    output_dir = export_dir / str(uuid.uuid4())
    output_dir.mkdir(parents=True)
    output = output_dir / ("game.exe" if sys.platform == "win32" else "game")
    command = [
        GODOT,
        "--headless",
        "--path",
        str(PROJECT),
        "--export-debug",
        EXPORT_PRESET,
        str(output),
    ]
    if run_and_watch(command) != 0:
        return None
    if not output.is_file():
        print(f"导出产物不存在：{output}", file=sys.stderr)
        return None
    return output


def launch_command(binary: Path, scene: str) -> list[str]:
    return [str(binary), "--", f"--test={scene}"]


def run_and_watch(command: list[str]) -> int:
    process = subprocess.Popen(
        command,
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
