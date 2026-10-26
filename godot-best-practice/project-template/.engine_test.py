#!/usr/bin/env python3
"""用项目里的 .engine.bat / .engine.sh 导出 debug 包并跑测试。

  python .engine_test.py
  python .engine_test.py --id-smoke
  python .engine_test.py --all

不带参数跑 smoke。--all 并发跑 tests 目录下一层、文件名不以 _ 开头的全部 gd。
出现错误或警告立刻结束该测试项。--all 里有一项失败就停掉其余项。
时间上限写在 GDScript 入口里，不在这里。
Autoload tests/_test_entry.gd 读取 --test=res://....gd，load 后 new() 挂到自己下面。测试不使用 tscn。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ENGINE = PROJECT / (".engine.bat" if sys.platform == "win32" else ".engine.sh")
EXPORT_PRESET = "Windows Desktop Test" if sys.platform == "win32" else "Linux Desktop Test"
TESTS_DIRECTORY = PROJECT / "tests"
DEFAULT_TEST = "smoke"

OFFENDING_PREFIXES = (
    "SCRIPT ERROR:",
    "ERROR:",
    "WARNING:",
    "USER WARNING:",
    "USER ERROR:",
)


def discover_tests() -> dict[str, str]:
    found: dict[str, str] = {}
    if not TESTS_DIRECTORY.is_dir():
        return found
    for path in sorted(TESTS_DIRECTORY.glob("*.gd")):
        if path.name.startswith("_"):
            continue
        found[path.stem] = f"res://tests/{path.name}"
    return found


def main(argv: list[str] | None = None) -> int:
    tests = discover_tests()
    parser = argparse.ArgumentParser(description="导出 debug 包并跑测试")
    parser.add_argument("--all", action="store_true", help="并发跑 tests 目录下全部测试")
    for name in tests:
        parser.add_argument(f"--id-{name}", dest=name, action="store_true", help=tests[name])
    args = parser.parse_args(argv)
    selected = [name for name in tests if getattr(args, name)]
    if args.all and selected:
        print("一次只能跑一个测试，或使用 --all", file=sys.stderr)
        return 2
    if not args.all:
        if not selected:
            selected = [DEFAULT_TEST]
        if len(selected) != 1 or selected[0] not in tests:
            names = " ".join(f"--id-{name}" for name in tests)
            print(f"一次只能跑一个测试，可选：{names} --all", file=sys.stderr)
            return 2
    export_directory = create_export_directory()
    names = list(tests) if args.all else selected
    return run_tests(names, tests, export_directory, concurrent=args.all)


def create_export_directory() -> Path:
    export_directory = (
        Path(tempfile.gettempdir()) / PROJECT.name / "test" / f"export_{uuid.uuid4()}"
    )
    export_directory.mkdir(parents=True)
    return export_directory


def run_tests(
    names: list[str],
    tests: dict[str, str],
    export_directory: Path,
    concurrent: bool,
) -> int:
    export_log = export_directory / "export.txt"
    binary = export_debug(export_directory, export_log, None, None, None)
    export_text = export_log.read_text(encoding="utf-8") if export_log.is_file() else ""
    export_log.unlink(missing_ok=True)
    if binary is None:
        name = names[0]
        log_path = test_log_path(export_directory, name)
        log_path.write_text(export_text, encoding="utf-8")
        print(f"{name}测试失败, 详细报告见{log_path}", file=sys.stderr)
        return 1

    cancel = threading.Event()
    processes: list[subprocess.Popen[str]] = []
    processes_lock = threading.Lock()
    failure_lock = threading.Lock()
    failed_name: list[str] = []

    def run_named(name: str) -> int:
        if cancel.is_set():
            return 1
        run_directory = export_directory / "tests" / name
        log_path = test_log_path(export_directory, name)
        log_path.write_text(export_text, encoding="utf-8")
        code = run_and_watch(
            launch_command(binary, tests[name], run_directory),
            log_path,
            cancel if concurrent else None,
            processes if concurrent else None,
            processes_lock if concurrent else None,
            run_directory,
        )
        if code != 0 and concurrent:
            with failure_lock:
                if not cancel.is_set():
                    failed_name.append(name)
                    cancel.set()
                    stop_registered(processes, processes_lock)
        elif code != 0:
            failed_name.append(name)
        return code

    if concurrent:
        with ThreadPoolExecutor(max_workers=max(len(names), 1)) as pool:
            codes = [future.result() for future in [pool.submit(run_named, name) for name in names]]
    else:
        codes = [run_named(name) for name in names]
    if failed_name:
        name = failed_name[0]
        print(
            f"{name}测试失败, 详细报告见{test_log_path(export_directory, name)}",
            file=sys.stderr,
        )
        return 1
    if any(code != 0 for code in codes):
        return 1
    return 0


def test_log_path(export_directory: Path, name: str) -> Path:
    log_path = export_directory / "tests" / name / "test_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def export_debug(
    export_dir: Path,
    log_path: Path,
    cancel: threading.Event | None,
    processes: list[subprocess.Popen[str]] | None,
    processes_lock: threading.Lock | None,
) -> Path | None:
    export_dir.mkdir(parents=True, exist_ok=True)
    output = export_dir / ("game.exe" if sys.platform == "win32" else "game")
    command = engine_command(
        "--headless",
        "--path",
        str(PROJECT),
        "--export-debug",
        EXPORT_PRESET,
        str(output),
    )
    if run_and_watch(command, log_path, cancel, processes, processes_lock) != 0:
        return None
    binary = exported_binary(output)
    if binary is None:
        message = f"导出产物不存在：{output}\n"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(message)
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


def launch_command(binary: Path, scene: str, run_directory: Path) -> list[str]:
    return [
        str(binary),
        "--",
        f"--test={scene}",
        f"--run-directory={run_directory}",
    ]


def run_and_watch(
    command: list[str],
    log_path: Path,
    cancel: threading.Event | None = None,
    processes: list[subprocess.Popen[str]] | None = None,
    processes_lock: threading.Lock | None = None,
    working_directory: Path | None = None,
) -> int:
    if cancel is not None and cancel.is_set():
        return 1
    process = subprocess.Popen(
        command,
        cwd=working_directory or PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    register(process, processes, processes_lock)
    log_file = log_path.open("a", encoding="utf-8")
    offending = False
    assert process.stdout is not None
    try:
        for raw_line in process.stdout:
            if cancel is not None and cancel.is_set():
                stop(process)
                break
            log_file.write(raw_line)
            log_file.flush()
            if processes is None:
                sys.stdout.write(raw_line)
                sys.stdout.flush()
            line = raw_line.strip()
            if any(line.startswith(prefix) for prefix in OFFENDING_PREFIXES):
                offending = True
                stop(process)
                notice = f"日志出现错误或警告，已停止：{line}\n"
                log_file.write(notice)
                log_file.flush()
                if processes is None:
                    print(notice, file=sys.stderr, end="")
                break
    finally:
        log_file.close()
    return_code = process.wait()
    unregister(process, processes, processes_lock)
    if offending or (cancel is not None and cancel.is_set() and return_code != 0):
        return 1
    if cancel is not None and cancel.is_set():
        return 1
    return return_code


def register(
    process: subprocess.Popen[str],
    processes: list[subprocess.Popen[str]] | None,
    processes_lock: threading.Lock | None,
) -> None:
    if processes is None or processes_lock is None:
        return
    with processes_lock:
        processes.append(process)


def unregister(
    process: subprocess.Popen[str],
    processes: list[subprocess.Popen[str]] | None,
    processes_lock: threading.Lock | None,
) -> None:
    if processes is None or processes_lock is None:
        return
    with processes_lock:
        if process in processes:
            processes.remove(process)


def stop_registered(
    processes: list[subprocess.Popen[str]],
    processes_lock: threading.Lock,
) -> None:
    with processes_lock:
        running = list(processes)
    for process in running:
        stop(process)


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
