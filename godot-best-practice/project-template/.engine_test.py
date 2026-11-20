#!/usr/bin/env python3
"""用项目里的引擎导出 debug 包并跑测试（.engine.py 只负责定位并下载引擎）。

  python .engine_test.py
  python .engine_test.py --id-smoke
  python .engine_test.py --id smoke road_network
  python .engine_test.py --id smoke --id road_network --jobs 1
  python .engine_test.py --all
  python .engine_test.py --all --fail-fast
  python .engine_test.py --all --jobs 6 --timing

不带参数跑 smoke。--id 点名一个或多个测试，空格分隔，也可以重复给；--id-<名字> 等价于点它一项。
点名一项时前台串行跑；点名多项时与 --all 一样并发（--jobs 控进程数、失败不中断其余项，
日志写 <测试名>/<测试名>.log），--jobs 1 可把一批压成一前一后。
--all 并发跑 tests 目录下一层、文件名不以 _ 开头的全部 gd。
出现错误或警告立刻结束该测试项。--all 默认等全部跑完，失败项最后逐条列出，有失败退出码 1；
--fail-fast 则第一个失败就停掉其余测试。

只报结论：全部通过时只打印总耗时（--timing 再多打一张逐项耗时表）；失败时才打印错误、
失败项的日志路径与日志尾部。模板下载、导入、编译、导出与逐项成功的过程输出一律不往终端打。

条目上限、单项与全量时间上限、并发都读 project.godot 的 [test]，缺省时用内置默认值：
max_tests=32、test_timeout_minutes=1、total_timeout_minutes=5、jobs=4。--jobs 可覆盖 jobs。
--all 的条目数超过 max_tests 直接报错。时间上限没有 CLI 开关：单项超过 test_timeout_minutes、
--all 超过 total_timeout_minutes 都由脚本强杀进程，并打印「测试超时，请精简测试项。禁止修改测试用时。」。
测试脚本不自己写时间上限，也不能靠放宽上限过关。
每个测试进程一结束就把「<测试名> 用时 <秒> 退出码 <码>」记进 timings.csv；全部跑完写明细并只报总计。
一批里实际跑完的项（跳过与超时不计）若 max - min > max * 0.5，--timing 会提示把各测试项
耗时规划得尽量接近，以发挥并发优势。
跑前先查被跟踪的 *.uid 与 *.import：源文件已经删掉的元数据一律报错并一次列出全部路径，
Godot 删脚本或资源时不会回收同名元数据，留着只会误导编辑器的导入。
跑完后若工作区还有未提交的文件（含未跟踪且未被 ignore），也会报错，避免测试残留或忘记提交。
产物固定放在项目的 .export/test/ 下，可执行文件按项目名命名。每次开跑覆盖同名产物。
每次运行建一个独立的 .export/.test_<GUID>/：
测试日志写 <测试名>/<测试名>.log，每个测试的运行目录是 <测试名>/，开跑前清空；user:// 放在包目录的 user_data/<测试名>/，随包删除。
测试跑完删除整个 .export/test/ 目录，只保留 .test_<GUID>/。
timings.csv（name,seconds,code,boot_ms）只作明细：seconds 是整个测试进程的墙钟，boot_ms 是
_test_entry.gd 挂测试节点前的启动段（引擎 + autoload + 主场景），两者相减得到用例本体；
--timing 再把逐项耗时按降序打一张表。
导入、构建、导出的引擎输出写 .test_<GUID>/export.log，失败时打印日志尾部。
导出阶段只看引擎退出码与产物是否存在：引擎自己在着色器/资源上打的 ERROR 由它继续处理，不算导出失败。
导出直接调引擎，不经 .engine.py 转交：转交层把任何 ERROR 都当成硬错误提前杀掉引擎。
导出预设按平台选：win32 用 Windows Desktop Test，darwin 用 macOS Desktop Test（.app 目录），
其余用 Linux Desktop Test。导出产物跨调用不缓存：实测导出只占全量墙钟的 1.8%（6.5s / 359.7s），低于缓存阈值（15%）。
dotnet=true 时先导入资源、再跑一次 --build-solutions，然后才导出：全新检出既没有 .godot 导入产物
也没有 C# 程序集和全局类缓存，不先导入引擎起不来，不构建 GDScript 会解析不到 C# 的 [GlobalClass]；
导出模板也按 mono_export_templates.tpz 下载。
导出只用 .godot/imported 里已有的导入产物，引擎不会自己导入；全新检出（含每个新 worktree）
没有这份缓存，所以缓存为空时脚本先跑一次 --import（首次约 30–45s，之后零成本）。
--reimport 强制先重导一遍再导出，用于缓存过期（[engine_host] 版本升过、导入被打断）的情形。
导入段不计入总计 / 导出毫秒数，失败就退出 1，不带着空缓存去导出。
测试进程的 user:// 指到各自运行目录下的 user_data：同批并发与两条 --all 同时跑都各一份，夹具表与渲染缓存互不覆盖。
冷缓存时（首次导入）不要并跑两路 --all：它们会同时写同一份 .godot。
Autoload _test_entry.gd 读取 --test=res://....gd，load 后 new() 挂到自己下面。测试不使用 tscn。
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import difflib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ENGINE = PROJECT / ".engine.py"
TESTS_DIRECTORY = PROJECT / "tests"
EXPORT_ROOT = PROJECT / ".export"
PACKAGE_DIRECTORY_NAME = "test"
# 导出只认 .godot/imported 里已有的导入产物，不自己导入；全新检出没有这份缓存。
IMPORT_CACHE_DIRECTORY = PROJECT / ".godot" / "imported"
# 每次运行一个独立的 .test_<GUID>，日志、截图与运行目录不跨次覆盖。
LOG_DIRECTORY = EXPORT_ROOT / f".test_{uuid.uuid4().hex}"
EXPORT_LOG_NAME = "export.log"
DEFAULT_TEST = "smoke"
# project.godot [test] 的缺省值：字段缺失时用这些，不报错。
TEST_CONFIG_DEFAULTS = {
    "max_tests": "32",
    "test_timeout_minutes": "1",
    "total_timeout_minutes": "5",
    "jobs": "4",
}
# --fail-fast 下因前面的测试失败而没跑完的项用这个退出码，不计入失败列表。
SKIPPED_EXIT_CODE = -1
# 单项超过 test_timeout_minutes 时用这个退出码，计入失败列表。
TIMEOUT_EXIT_CODE = -2
TIMINGS_FILE_NAME = "timings.csv"
# 超时一律强杀进程，不给跳过/延长/关闭的开关；这句原文必须打出来。
TIMEOUT_NOTICE = "测试超时，请精简测试项。禁止修改测试用时。"
BALANCE_NOTICE = "请合理规划测试项，使每个测试项耗时尽可能相同，以充分发挥并发优势"
# 删除脚本或资源后 Godot 不回收同名元数据：*.uid 跟着脚本与资源，*.import 跟着导入资源。
METADATA_SUFFIXES = (".uid", ".import")
# 失败时最多打印多少行日志尾部：错误与中止提示总在尾部。
LOG_TAIL_LINES = 40
# _test_entry.gd 在挂测试节点前打一行 TEST_TIMING boot_ms=<毫秒>，用来把每个进程的启动成本
# 从用例耗时里分出来。这行不带 ERROR/WARNING 前缀，不触发即停判定。
BOOT_TIMING_PATTERN = re.compile(r"TEST_TIMING boot_ms=(\d+)")


def export_preset_name() -> str:
    """导出预设不能跨平台：Windows 包是 PE，Linux 包是 ELF，macOS 包是 .app 目录。"""
    if sys.platform == "win32":
        return "Windows Desktop Test"
    if sys.platform == "darwin":
        return "macOS Desktop Test"
    return "Linux Desktop Test"


OFFENDING_PREFIXES = (
    "SCRIPT ERROR:",
    "ERROR:",
    "WARNING:",
    "USER WARNING:",
    "USER ERROR:",
)


def quiet(call):
    """成功时不输出：prepare_engine 会报「引擎已存在」这类进度，成功路径要静默。"""
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stderr(buffer):
            return call()
    except Exception:
        sys.stderr.write(buffer.getvalue())
        raise


def print_text_tail(text: str, source: str = "", tail_lines: int = LOG_TAIL_LINES) -> None:
    """只打尾部：失败时最需要看的是最后一屏，完整内容留在日志文件里。"""
    lines = text.splitlines()
    if not lines:
        return
    if len(lines) > tail_lines:
        where = f"，完整日志见 {source}" if source else ""
        print(f"……仅显示最后 {tail_lines} 行{where}", file=sys.stderr)
        lines = lines[-tail_lines:]
    print("\n".join(lines), file=sys.stderr)


def print_log_tail(log_path: Path, tail_lines: int = LOG_TAIL_LINES) -> None:
    if log_path.is_file():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        print_text_tail(text, str(log_path), tail_lines)


def discover_tests() -> dict[str, str]:
    found: dict[str, str] = {}
    if not TESTS_DIRECTORY.is_dir():
        return found
    for path in sorted(TESTS_DIRECTORY.glob("*.gd")):
        if path.name.startswith("_"):
            continue
        found[path.stem] = f"res://tests/{path.name}"
    return found


def merge_selection(args, tests: dict[str, str]) -> list[str]:
    """--id 的点名列表与旧的 --id-<名字> 开关合并，按给定顺序去重。"""
    ordered = list(args.ids or [])
    ordered.extend(name for name in tests if getattr(args, name))
    unique: list[str] = []
    for name in ordered:
        if name not in unique:
            unique.append(name)
    return unique


def report_unknown_tests(unknown: list[str], tests: dict[str, str]) -> None:
    """未知 id 逐条报，附相近名，最后给总项数提示。"""
    for name in unknown:
        matches = difflib.get_close_matches(name, tests, n=3)
        hint = "；相近的：{}".format("、".join(matches)) if matches else ""
        print(f"没有这个测试 id：{name}{hint}", file=sys.stderr)
    print(f"测试共 {len(tests)} 项：--all 跑全部，--id <名字>... 点名一批", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    engine_module = load_engine_module()
    limits = load_test_limits(engine_module)
    tests = discover_tests()
    parser = argparse.ArgumentParser(description="导出 debug 包并跑测试")
    parser.add_argument("--all", action="store_true", help="并发跑 tests 目录下全部测试")
    parser.add_argument(
        "--jobs",
        type=positive_int,
        default=None,
        metavar="N",
        help=f"同时运行的测试进程数，默认 {limits['jobs']}（project.godot [test] jobs）",
    )
    parser.add_argument("--timing", action="store_true", help="打印按耗时降序的逐项表")
    parser.add_argument(
        "--reimport", action="store_true", help="导出前强制重新导入资源（.godot 缓存过期时用）"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="一批里第一个失败就停止其余测试（--all 与多项 --id 都适用）",
    )
    parser.add_argument(
        "--id",
        dest="ids",
        nargs="+",
        action="extend",
        metavar="NAME",
        help="点名一个或多个测试，空格分隔；可重复给，等价于 --id-<名字> 给一个",
    )
    for name in tests:
        parser.add_argument(f"--id-{name}", dest=name, action="store_true", help=tests[name])
    args = parser.parse_args(argv)
    selected = merge_selection(args, tests)
    if args.all and selected:
        print("--all 不能再带 --id：要么跑全部，要么点名一批", file=sys.stderr)
        return 2
    unknown = [name for name in selected if name not in tests]
    if unknown:
        report_unknown_tests(unknown, tests)
        return 2
    if args.all and len(tests) > limits["max_tests"]:
        print(
            f"--all 有 {len(tests)} 个测试条目，超过上限 {limits['max_tests']}"
            "（project.godot [test] max_tests）。请合并测试条目。",
            file=sys.stderr,
        )
        return 2
    orphans = orphaned_metadata_files()
    if orphans:
        print("这些元数据文件的源文件已经不在工作区，Godot 编辑器不会再清理它们：", file=sys.stderr)
        for path in orphans:
            print(f"  {path}", file=sys.stderr)
        return 1
    executable = prepare_export_templates(engine_module)
    # 全新检出的 .godot 缓存是空的：先导入，再编译 C#，否则引擎起不来也解析不到 [GlobalClass]。
    if not ensure_imported(executable, args.reimport):
        return 1
    if not build_project(engine_module, executable):
        return 1
    export_directory = create_export_directory()
    names = list(tests) if args.all else (selected or [DEFAULT_TEST])
    concurrent = len(names) > 1
    jobs = args.jobs or limits["jobs"]
    result = run_tests(
        names,
        tests,
        export_directory,
        executable,
        concurrent=concurrent,
        jobs=jobs,
        show_timing=args.timing,
        fail_fast=args.fail_fast,
        test_timeout_seconds=limits["test_timeout_seconds"],
        total_timeout_seconds=limits["total_timeout_seconds"] if args.all else None,
    )
    dirty = uncommitted_files()
    if dirty:
        print("测试跑完后工作区还有未提交的文件（含未跟踪且未被 ignore）：", file=sys.stderr)
        for line in dirty:
            print(f"  {line}", file=sys.stderr)
        return 1
    return result


def uncommitted_files() -> list[str]:
    """返回未提交或未跟踪且未被 ignore 的文件；不是 git 仓库或没有 git 时返回空。"""
    status = git_output(["status", "--porcelain", "--untracked-files=all"])
    if status is None:
        return []
    return [line for line in status.splitlines() if line.strip()]


def orphaned_metadata_files() -> list[str]:
    """返回源文件已不在工作区的被跟踪元数据；不是 git 仓库或没有 git 时返回空。"""
    tracked = git_output(["ls-files", "--", *[f"*{suffix}" for suffix in METADATA_SUFFIXES]])
    if tracked is None:
        return []
    orphans: list[str] = []
    for metadata_path in tracked.splitlines():
        metadata_path = metadata_path.strip()
        suffix = Path(metadata_path).suffix
        if not metadata_path or suffix not in METADATA_SUFFIXES:
            continue
        if not (PROJECT / metadata_path[: -len(suffix)]).exists():
            orphans.append(metadata_path)
    return orphans


def git_output(arguments: list[str]) -> str | None:
    """跑一条只读 git 命令；不是 git 仓库或没有 git 时返回 None，调用方据此跳过检查。"""
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=PROJECT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    return completed.stdout if completed.returncode == 0 else None


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("--jobs 至少是 1")
    return value


def load_test_limits(engine_module) -> dict[str, float]:
    """读 project.godot [test]；缺字段用 TEST_CONFIG_DEFAULTS。"""
    values = engine_module.read_config_section("test", TEST_CONFIG_DEFAULTS)
    try:
        limits = {
            "max_tests": int(values["max_tests"]),
            "jobs": int(values["jobs"]),
            "test_timeout_seconds": float(values["test_timeout_minutes"]) * 60.0,
            "total_timeout_seconds": float(values["total_timeout_minutes"]) * 60.0,
        }
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"project.godot [test] 配置无效：{error}") from error
    if limits["max_tests"] < 1 or limits["jobs"] < 1:
        raise RuntimeError("project.godot [test] 的 max_tests 与 jobs 至少是 1")
    if limits["test_timeout_seconds"] <= 0 or limits["total_timeout_seconds"] <= 0:
        raise RuntimeError("project.godot [test] 的时间上限必须大于 0")
    return limits


def load_engine_module():
    spec = importlib.util.spec_from_file_location("project_engine", ENGINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {ENGINE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_export_templates(engine_module) -> Path:
    executable = quiet(engine_module.prepare_engine)
    version_result = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    template_version = version_result.stdout.strip().split(".official", 1)[0]
    if not template_version:
        raise RuntimeError(f"无法解析导出模板版本：{version_result.stdout!r}")
    templates_directory = godot_export_templates_directory(template_version)
    if (templates_directory / "version.txt").is_file():
        return executable
    if templates_directory.exists():
        shutil.rmtree(templates_directory)
    templates_directory.mkdir(parents=True)
    config = engine_module.load_engine_config()
    template_slug = (
        "mono_export_templates.tpz"
        if engine_module.uses_dotnet(config)
        else "export_templates.tpz"
    )
    archive_path = templates_directory / "export_templates.tpz"
    download_url = (
        "https://downloads.godotengine.org/"
        f"?version={config['version']}&flavor={config['flavor']}&slug={template_slug}"
    )
    request = urllib.request.Request(download_url, headers={"User-Agent": "godot-best-practice"})
    with urllib.request.urlopen(request) as response, archive_path.open("wb") as archive_file:
        shutil.copyfileobj(response, archive_file)
    extract_directory = templates_directory / "extract"
    extract_directory.mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extract_directory)
    packed_templates = extract_directory / "templates"
    if not packed_templates.is_dir():
        raise RuntimeError(f"导出模板压缩包里没有 templates 目录：{archive_path}")
    for child in packed_templates.iterdir():
        shutil.move(str(child), templates_directory / child.name)
    shutil.rmtree(extract_directory)
    archive_path.unlink()
    if not (templates_directory / "version.txt").is_file():
        raise RuntimeError(f"导出模板缺少 version.txt：{templates_directory}")
    return executable


def build_project(engine_module, executable: Path) -> bool:
    """dotnet 工程先编译 C# 解决方案：全新检出没有 C# 程序集，GDScript 会解析不到 [GlobalClass]。

    不用 .engine.py 转交：构建期引擎会因 C# Autoload 尚未编译而打 ERROR，那是正常现象，
    转交层会把它当成硬错误提前停掉引擎。这里直接跑引擎，只看程序集有没有产出。
    """
    if not engine_module.uses_dotnet():
        return True
    completed = subprocess.run(
        [str(executable), "--headless", "--path", str(PROJECT), "--build-solutions", "--quit"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assembly = project_assembly_path(engine_module)
    if not assembly.is_file():
        print(
            f"C# 没有编译出 {assembly}（引擎退出码 {completed.returncode}），构建输出如下：",
            file=sys.stderr,
        )
        print_text_tail(completed.stdout + completed.stderr)
        return False
    return True


def project_assembly_path(engine_module) -> Path:
    """[dotnet] project/assembly_name 决定程序集名；缺字段时按 Godot 默认取项目名。"""
    dotnet = engine_module.read_config_section("dotnet", {})
    assembly_name = dotnet.get("project/assembly_name", "").strip()
    if not assembly_name:
        application = engine_module.read_config_section("application", {})
        assembly_name = application.get("config/name", "").strip() or PROJECT.name
    return PROJECT / ".godot" / "mono" / "temp" / "bin" / "Debug" / f"{assembly_name}.dll"


def godot_export_templates_directory(template_version: str) -> Path:
    if sys.platform == "win32":
        data_directory = Path(os.environ["APPDATA"]) / "Godot"
    elif sys.platform == "darwin":
        data_directory = Path.home() / "Library" / "Application Support" / "Godot"
    else:
        data_home = os.environ.get("XDG_DATA_HOME")
        data_directory = Path(data_home) if data_home else Path.home() / ".local" / "share"
        data_directory = data_directory / "godot"
    return data_directory / "export_templates" / template_version


def import_cache_ready() -> bool:
    """缓存为空的判定只看 .godot/imported 有没有条目：这正是全新检出的样子。"""
    return IMPORT_CACHE_DIRECTORY.is_dir() and any(IMPORT_CACHE_DIRECTORY.iterdir())


def ensure_imported(executable: Path, force: bool) -> bool:
    """缓存为空或 --reimport 时先导入一遍，补不上就是硬失败，不带着空缓存去导出。"""
    if force or not import_cache_ready():
        return import_project(executable)
    return True


def import_project(executable: Path) -> bool:
    """导入段成功时完全静默：干净环境下引擎也会打与测试无关的 ERROR 行。"""
    completed = subprocess.run(
        [str(executable), "--headless", "--path", str(PROJECT), "--import"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    imported = import_cache_ready()
    if completed.returncode != 0 or not imported:
        reason = "引擎退出码非 0" if completed.returncode != 0 else ".godot/imported 仍是空的"
        print(f"导入失败（{reason}，退出码 {completed.returncode}），导出会缺导入产物", file=sys.stderr)
        print_text_tail(completed.stdout + completed.stderr)
        return False
    return True


def create_export_directory() -> Path:
    """测试只跑本平台的包，固定放在 .export/test，跑完整目录删掉。"""
    export_directory = EXPORT_ROOT / PACKAGE_DIRECTORY_NAME
    export_directory.mkdir(parents=True, exist_ok=True)
    return export_directory


def export_log_path() -> Path:
    log_path = LOG_DIRECTORY / EXPORT_LOG_NAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def test_log_path(name: str) -> Path:
    log_path = LOG_DIRECTORY / name / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def test_run_directory(name: str) -> Path:
    """每个测试独立的运行目录，开跑前清空，避免上次的 user:// 与截图影响本次。"""
    run_directory = LOG_DIRECTORY / name
    shutil.rmtree(run_directory, ignore_errors=True)
    run_directory.mkdir(parents=True)
    return run_directory


# 测试进程的 user:// 根目录落在包目录的 user_data/<测试名> 里：同批 4 个进程各自一份，
# 夹具表、渲染缓存、存档与偏好不再互相删改；包目录测完整个删除，不会残留 user_data。
def isolated_user_data_environment(export_directory: Path, name: str) -> dict[str, str]:
    user_data_directory = export_directory / "user_data" / name
    user_data_directory.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    if sys.platform == "win32":
        environment["APPDATA"] = str(user_data_directory)
    elif sys.platform == "darwin":
        environment["HOME"] = str(user_data_directory)
    else:
        environment["XDG_DATA_HOME"] = str(user_data_directory)
    return environment


def run_tests(
    names: list[str],
    tests: dict[str, str],
    export_directory: Path,
    executable: Path,
    concurrent: bool,
    jobs: int,
    show_timing: bool,
    fail_fast: bool = False,
    test_timeout_seconds: float | None = None,
    total_timeout_seconds: float | None = None,
) -> int:
    started = time.monotonic()
    all_deadline = started + total_timeout_seconds if total_timeout_seconds else None
    processes: list[subprocess.Popen[str]] = []
    processes_lock = threading.Lock()
    all_timed_out = threading.Event()
    all_timer = None
    if all_deadline is not None:
        # 全量上限从导出前就开始算：导出卡住也要能被终止。
        all_timer = threading.Timer(
            max(0.0, all_deadline - time.monotonic()),
            lambda: (all_timed_out.set(), stop_registered(processes, processes_lock)),
        )
        all_timer.daemon = True
        all_timer.start()

    try:
        binary = export_debug(
            executable, export_directory, processes, processes_lock, all_deadline
        )
        if binary is None:
            remove_package_directory(export_directory)
            if all_timed_out.is_set():
                print(
                    f"--all 超过 {total_timeout_seconds / 60:g} 分钟上限，已终止",
                    file=sys.stderr,
                )
                print(TIMEOUT_NOTICE, file=sys.stderr)
            print_log_tail(export_log_path())
            return 1

        cancel = threading.Event() if concurrent and fail_fast else None
        cancel_lock = threading.Lock()

        def run_named(name: str) -> tuple[str, float, int, str]:
            run_directory = test_run_directory(name)
            log_path = test_log_path(name)
            if cancel is not None and cancel.is_set():
                log_path.write_text("前面的测试失败，已跳过本项\n", encoding="utf-8")
                return name, 0.0, SKIPPED_EXIT_CODE, ""
            if all_timed_out.is_set():
                log_path.write_text("--all 已到时间上限，本项未跑\n", encoding="utf-8")
                return name, 0.0, TIMEOUT_EXIT_CODE, ""
            test_started = time.monotonic()
            code = run_and_watch(
                launch_command(binary, tests[name], run_directory),
                log_path,
                working_directory=run_directory,
                environment=isolated_user_data_environment(export_directory, name),
                cancel=cancel,
                processes=processes,
                processes_lock=processes_lock,
                timeout_seconds=test_timeout_seconds,
                deadline=all_deadline,
            )
            seconds = time.monotonic() - test_started
            if code != 0 and cancel is not None:
                with cancel_lock:
                    if not cancel.is_set():
                        cancel.set()
                        stop_registered(processes, processes_lock)
            return name, seconds, code, boot_milliseconds(log_path)

        try:
            if concurrent:
                worker_count = min(jobs, max(len(names), 1))
                with ThreadPoolExecutor(max_workers=worker_count) as pool:
                    results = [
                        future.result()
                        for future in [pool.submit(run_named, name) for name in names]
                    ]
            else:
                results = [run_named(name) for name in names]
        finally:
            remove_package_directory(export_directory)
    finally:
        if all_timer is not None:
            all_timer.cancel()

    total_seconds = time.monotonic() - started
    write_timings(results)
    if show_timing:
        print_timing_table(results)
        print_balance_hint(results)
    problems = [result for result in results if result[2] not in (0, SKIPPED_EXIT_CODE)]
    failed = [name for name, _seconds, code, _boot in problems if code != TIMEOUT_EXIT_CODE]
    timed_out = [name for name, _seconds, code, _boot in problems if code == TIMEOUT_EXIT_CODE]
    skipped = [
        name for name, _seconds, code, _boot in results if code == SKIPPED_EXIT_CODE
    ]
    if all_timed_out.is_set():
        print(
            f"--all 超过 {total_timeout_seconds / 60:g} 分钟上限，已终止；本轮结果不作通过依据",
            file=sys.stderr,
        )
        print(TIMEOUT_NOTICE, file=sys.stderr)
        print_problem_reports(problems)
        return 1
    if timed_out:
        limit = f"{test_timeout_seconds / 60:g} 分钟" if test_timeout_seconds else "上限"
        print(f"单项超过 {limit}：{'、'.join(timed_out)}", file=sys.stderr)
    if failed:
        for name, _seconds, code, _boot in problems:
            if code == TIMEOUT_EXIT_CODE:
                continue
            print(f"{name} 测试失败（退出码 {code}），日志：{test_log_path(name)}", file=sys.stderr)
        print(f"共 {len(names)} 项，失败 {len(failed)} 项：{'、'.join(failed)}", file=sys.stderr)
        if skipped:
            print(f"已跳过 {len(skipped)} 项：{'、'.join(skipped)}", file=sys.stderr)
    if problems:
        print_problem_reports(problems)
        return 1
    # 全部通过：只报总耗时，过程输出都在 .export/.test_<GUID>/ 里。
    print(f"总计 {total_seconds:.1f}s")
    return 0


def print_problem_reports(results: list[tuple[str, float, int, str]]) -> None:
    """失败项逐个打日志尾部：成功时一个字节都不打，失败时把错误完整交出来。"""
    for name, _seconds, _code, _boot in results:
        log_path = test_log_path(name)
        print(f"—— {name} 日志尾部（{log_path}）——", file=sys.stderr)
        print_log_tail(log_path)


def write_timings(results: list[tuple[str, float, int, str]]) -> Path:
    """本轮每个测试一行的计时明细：seconds 含进程启动与用例本体，boot_ms 只算启动段。"""
    timings_path = LOG_DIRECTORY / TIMINGS_FILE_NAME
    timings_path.parent.mkdir(parents=True, exist_ok=True)
    with timings_path.open("w", encoding="utf-8", newline="") as timings_file:
        writer = csv.writer(timings_file)
        writer.writerow(["name", "seconds", "code", "boot_ms"])
        for name, seconds, code, boot_ms in results:
            writer.writerow([name, f"{seconds:.3f}", code, boot_ms])
    return timings_path


def executed_seconds(results: list[tuple[str, float, int, str]]) -> list[float]:
    """只取实际跑完的项：跳过与超时没有可信的用例耗时，不参与均衡性判断。"""
    return [
        seconds
        for _name, seconds, code, _boot in results
        if code not in (SKIPPED_EXIT_CODE, TIMEOUT_EXIT_CODE)
    ]


def print_balance_hint(results: list[tuple[str, float, int, str]]) -> None:
    """最长与最短相差过半时提示重划测试项：并发收益全被最慢的一项吃掉。"""
    seconds = executed_seconds(results)
    if len(seconds) < 2:
        return
    longest = max(seconds)
    if longest - min(seconds) > longest * 0.5:
        print(BALANCE_NOTICE)


def print_timing_table(results: list[tuple[str, float, int, str]]) -> None:
    rows = sorted(results, key=lambda result: result[1], reverse=True)
    print(f"{'测试':<34}{'秒':>8}{'启动ms':>10}{'退出码':>8}")
    for name, seconds, code, boot_ms in rows:
        print(f"{name:<34}{seconds:>8.2f}{boot_ms or '-':>10}{code:>8}")
    boot_values = sorted(int(boot) for _name, _seconds, _code, boot in results if boot)
    if boot_values:
        print(
            "启动段中位数 {}ms / 最大 {}ms".format(median(boot_values), boot_values[-1])
        )


def median(values: list[int]) -> int:
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) // 2


def boot_milliseconds(log_path: Path) -> str:
    if not log_path.is_file():
        return ""
    match = BOOT_TIMING_PATTERN.search(log_path.read_text(encoding="utf-8", errors="replace"))
    return match.group(1) if match else ""


def export_output_path(export_dir: Path) -> Path:
    if sys.platform == "win32":
        return export_dir / f"{PROJECT.name}.exe"
    if sys.platform == "darwin":
        return export_dir / f"{PROJECT.name}.app"
    return export_dir / PROJECT.name


def remove_package_directory(export_directory: Path) -> None:
    """测完删掉整个包目录，只留 .export/.test_<GUID> 下的日志与运行目录。"""
    shutil.rmtree(export_directory, ignore_errors=True)


def export_debug(
    executable: Path,
    export_dir: Path,
    processes: list[subprocess.Popen[str]] | None = None,
    processes_lock: threading.Lock | None = None,
    deadline: float | None = None,
) -> Path | None:
    """直接调引擎导出：.engine.py 转交会把导出期的非致命 ERROR 当硬失败杀掉引擎。"""
    export_dir.mkdir(parents=True, exist_ok=True)
    output = export_output_path(export_dir)
    log_path = export_log_path()
    command = [
        str(executable),
        "--headless",
        "--path",
        str(PROJECT),
        "--export-debug",
        export_preset_name(),
        str(output),
    ]
    code = run_and_watch(
        command,
        log_path=log_path,
        processes=processes,
        processes_lock=processes_lock,
        deadline=deadline,
        # 导出阶段引擎会为着色器/资源打 ERROR 但自己继续，产物照样写出：只认退出码与产物。
        watch_offending=False,
    )
    binary = exported_binary(output)
    if binary is None:
        reason = f"退出码 {code}" if code != 0 else "产物不存在"
        print(f"导出失败（{reason}），日志：{log_path}", file=sys.stderr)
        return None
    return binary


def exported_binary(output: Path) -> Path | None:
    if sys.platform == "win32":
        console = output.with_name(output.stem + ".console.exe")
        if console.is_file():
            return console
    if sys.platform == "darwin":
        return macos_binary(output)
    if output.is_file():
        return output
    return None


def macos_binary(output: Path) -> Path | None:
    """macOS 导出产物是 .app 目录，可执行文件在 Contents/MacOS/ 下，名字取自 app 名。"""
    if output.is_file():
        return output
    macos_directory = output / "Contents" / "MacOS"
    if not macos_directory.is_dir():
        return None
    candidates = sorted(
        path for path in macos_directory.iterdir() if path.is_file() and os.access(path, os.X_OK)
    )
    return candidates[0] if candidates else None


def launch_command(binary: Path, scene: str, run_directory: Path) -> list[str]:
    command = [str(binary), "--audio-driver", "Dummy"]
    if sys.platform.startswith("linux"):
        command.extend(["--display-driver", "headless"])
    command.extend(
        [
            "--",
            f"--test={scene}",
            f"--run-directory={run_directory}",
        ]
    )
    return command


def run_and_watch(
    command: list[str],
    log_path: Path | None,
    working_directory: Path | None = None,
    environment: dict[str, str] | None = None,
    cancel: threading.Event | None = None,
    processes: list[subprocess.Popen[str]] | None = None,
    processes_lock: threading.Lock | None = None,
    timeout_seconds: float | None = None,
    deadline: float | None = None,
    watch_offending: bool = True,
) -> int:
    if cancel is not None and cancel.is_set():
        return SKIPPED_EXIT_CODE
    if deadline is not None and time.monotonic() >= deadline:
        return TIMEOUT_EXIT_CODE
    limit = None
    if timeout_seconds is not None:
        limit = time.monotonic() + timeout_seconds
    if deadline is not None:
        limit = deadline if limit is None else min(limit, deadline)
    process = subprocess.Popen(
        command,
        cwd=working_directory or PROJECT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    register_process(process, processes, processes_lock)
    timed_out = threading.Event()
    timer = None
    if limit is not None:
        # 到点强杀进程：没有跳过/延长/关闭超时的开关，只能精简测试项。
        timer = threading.Timer(
            max(0.0, limit - time.monotonic()),
            lambda: (timed_out.set(), stop(process)),
        )
        timer.daemon = True
        timer.start()
    log_file = log_path.open("w", encoding="utf-8") if log_path is not None else None

    def write_log(text: str) -> None:
        if log_file is not None:
            log_file.write(text)
            log_file.flush()

    offending = False
    cancelled = False
    assert process.stdout is not None
    try:
        for raw_line in process.stdout:
            if cancel is not None and cancel.is_set():
                cancelled = True
                stop(process)
                write_log("前面的测试失败，已停止本项\n")
                break
            write_log(raw_line)
            line = raw_line.strip()
            if watch_offending and any(line.startswith(prefix) for prefix in OFFENDING_PREFIXES):
                offending = True
                stop(process)
                write_log(f"日志出现错误或警告，已停止：{line}\n")
                break
    finally:
        if timer is not None:
            timer.cancel()
        if timed_out.is_set():
            write_log(f"{TIMEOUT_NOTICE}\n")
            print(TIMEOUT_NOTICE, file=sys.stderr, flush=True)
        if log_file is not None:
            log_file.close()
    return_code = process.wait()
    unregister_process(process, processes, processes_lock)
    if offending:
        return 1
    if timed_out.is_set():
        return TIMEOUT_EXIT_CODE
    if cancelled or (cancel is not None and cancel.is_set()):
        return SKIPPED_EXIT_CODE
    return return_code


def register_process(
    process: subprocess.Popen[str],
    processes: list[subprocess.Popen[str]] | None,
    processes_lock: threading.Lock | None,
) -> None:
    if processes is None or processes_lock is None:
        return
    with processes_lock:
        processes.append(process)


def unregister_process(
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
