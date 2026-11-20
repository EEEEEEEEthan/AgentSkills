#!/usr/bin/env python3
"""用项目里的引擎导出 debug 包并跑测试（.engine.py 只负责定位并下载引擎）。

  python .engine_test.py                          # a 档，等价 --id smoke
  python .engine_test.py --id-smoke
  python .engine_test.py --id smoke road_network
  python .engine_test.py --id smoke,road_network
  python .engine_test.py --id smoke --id road_network --jobs 1
  python .engine_test.py --ci                     # b 档，提交 / MR / CI
  python .engine_test.py --ci --fail-fast --timing
  python .engine_test.py --full                   # c 档，只给定时任务
  python .engine_test.py --export --id smoke      # 出包跑（诊断用，见下）

测试分三档，条目上限、并发与时间上限都写死在本文件，不再读 project.godot：

a 档（--id）   自测点名：默认 4 进程（--jobs 可覆盖），单项上限 30 分钟，无总上限。
               名字可用空格或逗号分隔（--id a,b,c）。点名一项时前台串行跑；点名多项时
               同样并发、同样受 --jobs 并发上限约束、同样无总时长上限（失败不中断其余项，
               日志写 <测试名>/<测试名>.log），--jobs 1 可把一批压成一前一后。
               --id-<名字> 等价于点它一项；不给任何选择时跑 smoke。
b 档（--ci）   CI 档：跑 tests/ 一层、文件名不以 _ 开头的全部 gd，并发限死 4（给 --jobs
               直接退出 2），无整轮时间上限。提交 / MR / CI 都用这一档。
c 档（--full） 全量档：跑 tests/ 一层全部 gd（含 _ 开头的条目），默认 4 进程，单项 30 分钟，
               整轮上限 2 小时。只给定时任务（每天一次）用，开发自测禁止跑 c 档。

--all 已退役：见到它直接退出 2 并指向 --ci / --full。
工具 / 夹具 / 预览 / 基类与建筑验收辅助脚本一律放 tests/tools/，任何档都不扫描该目录；
tests/ 一层只放能被 b 档发现的条目（extends TestScriptBase、文件名不以 _ 开头）。

出现错误或警告立刻结束该测试项。b/c 档默认等全部跑完，失败项最后逐条列出，有失败退出码 1；
--fail-fast 则第一个失败就停掉其余测试。

只报结论：全部通过时先打印「测试通过」再打总耗时（--timing 再多打一张逐项耗时表）；失败时才打印错误、
失败项的日志路径与日志尾部。模板下载、导入、编译、导出与逐项成功的过程输出一律不往终端打。

条目上限 32 对 b/c 档生效，超过直接报错。时间上限没有 CLI 开关：单项超过 30 分钟、c 档整轮
超过 2 小时都由脚本强杀进程，并打印「测试超时，请精简测试项。禁止修改测试用时。」。b 档没有整轮上限。
测试脚本不自己写时间上限，也不能靠放宽上限过关。
每个测试进程一结束就把「<测试名> 用时 <秒> 退出码 <码>」记进 timings.csv；全部跑完写明细并只报总计。
一批里实际跑完的项（跳过与超时不计）若 max - min > max * 0.5，--timing 会提示把各测试项
耗时规划得尽量接近，以发挥并发优势。
跑完后若工作区还有未提交的文件（含未跟踪且未被 ignore），只打一行「错误：测试完毕后工作区存在未提交文件」
并退出 1，避免测试残留或忘记提交；干净时再查失效的 .uid / .import 伴生文件，全部列出并退出 1。
产物固定放在项目的 .export/test/ 下，可执行文件按项目名命名。每次开跑覆盖同名产物。
每次运行建一个独立的 .export/.test_<GUID>/：
测试日志写 <测试名>/<测试名>.log，每个测试的运行目录是 <测试名>/，开跑前清空；user:// 放在包目录的 user_data/<测试名>/，随包删除。
测试跑完删除整个 .export/test/ 目录，只保留 .test_<GUID>/。
timings.csv（name,seconds,code,boot_ms）只作明细：seconds 是整个测试进程的墙钟，boot_ms 是
_test_entry.gd 挂测试节点前的启动段（引擎 + autoload + 主场景），两者相减得到用例本体；
--timing 再把逐项耗时按降序打一张表。
导入、构建、导出的引擎输出写 .test_<GUID>/export.log，失败时打印日志尾部。
默认宿主是编辑器可执行文件以项目运行模式直跑（带 editor 特性，不出包）；`--export` 才导出 debug 包
再在包里跑。出包路径目前只作诊断：实测包里 ui.tscn 嵌在 page_panel 实例里的 %OverviewMap 会整个丢，
UI 相关条目全红（项目自身的导出问题，与测试脚本无关）。
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
测试进程的 user:// 指到各自运行目录下的 user_data：同批并发与两条 b 档同时跑都各一份，夹具表与渲染缓存互不覆盖。
冷缓存时（首次导入）不要并跑两路 b 档：它们会同时写同一份 .godot。
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
# 扫失效 .uid / .import 时跳过的目录；嵌套带 project.godot 的子工程在遍历时另判。
SKIP_SOURCE_DIRECTORIES = {".git", ".godot", ".export", "node_modules"}
# 每次运行一个独立的 .test_<GUID>，日志、截图与运行目录不跨次覆盖。
LOG_DIRECTORY = EXPORT_ROOT / f".test_{uuid.uuid4().hex}"
EXPORT_LOG_NAME = "export.log"
DEFAULT_TEST = "smoke"
# 三档测试：a 点名（--id）、b CI（--ci）、c 全量（--full）。上限写死在本文件，
# 不再从 project.godot 的 [test] 读取：CI 的 4 线程是硬约束，不能被工程配置放宽；b 档不设整轮上限。
MAX_TESTS = 32
DEFAULT_JOBS = 4
CI_JOBS = 4
TEST_TIMEOUT_SECONDS = 30 * 60
FULL_TOTAL_TIMEOUT_SECONDS = 2 * 60 * 60
TIER_ID_LABEL = "a 档（--id）"
TIER_CI_LABEL = "b 档（--ci）"
TIER_FULL_LABEL = "c 档（--full）"
FULL_DISABLED_HINT = "c 档（--full）只给定时任务用，开发自测请用 --id 或 --ci"
# --fail-fast 下因前面的测试失败而没跑完的项用这个退出码，不计入失败列表。
SKIPPED_EXIT_CODE = -1
# 单项超过 TEST_TIMEOUT_SECONDS 时用这个退出码，计入失败列表。
TIMEOUT_EXIT_CODE = -2
TIMINGS_FILE_NAME = "timings.csv"
# 超时一律强杀进程，不给跳过/延长/关闭的开关；这句原文必须打出来。
TIMEOUT_NOTICE = "测试超时，请精简测试项。禁止修改测试用时。"
BALANCE_NOTICE = "请合理规划测试项，使每个测试项耗时尽可能相同，以充分发挥并发优势"
# 并发跑时相邻两个测试进程的启动间隔（秒）：同时启动的 4 个引擎会一起去建 Vulkan swapchain，
# 显存吃紧的机器上会随机报 VK_ERROR_OUT_OF_HOST_MEMORY。并发数不变，只错开启动。
LAUNCH_SPACING_SECONDS = 2.0
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


def discover_tests(include_underscored: bool = False) -> dict[str, str]:
    """只扫 tests/ 一层：b 档跳过 _ 开头的条目，c 档全收；子目录（tests/tools/）永不进档。"""
    found: dict[str, str] = {}
    if not TESTS_DIRECTORY.is_dir():
        return found
    for path in sorted(TESTS_DIRECTORY.glob("*.gd")):
        if path.name.startswith("_") and not include_underscored:
            continue
        found[path.stem] = f"res://tests/{path.name}"
    return found


def merge_selection(args, tests: dict[str, str]) -> list[str]:
    """--id 的点名列表（空格或逗号分隔）与旧的 --id-<名字> 开关合并，按给定顺序去重。"""
    ordered: list[str] = []
    for entry in args.ids or []:
        ordered.extend(part.strip() for part in entry.split(",") if part.strip())
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
    print(
        f"测试共 {len(tests)} 项：--ci 跑 b 档、--full 跑 c 档、--id <名字>... 点名一批",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    engine_module = load_engine_module()
    # c 档要连 _ 开头的条目也列出来，才能给它们生成 --id-<名字> 与全量列表；其它档只要 b 档可见的。
    raw_arguments = sys.argv[1:] if argv is None else list(argv)
    tests = discover_tests(include_underscored="--full" in raw_arguments)
    parser = argparse.ArgumentParser(description="导出 debug 包并跑三档测试")
    tier = parser.add_mutually_exclusive_group()
    tier.add_argument(
        "--ci",
        action="store_true",
        help=f"b 档：tests/ 一层非 _ 开头的全部条目，固定 {CI_JOBS} 线程、无整轮时间上限",
    )
    tier.add_argument(
        "--full",
        action="store_true",
        help=f"c 档：tests/ 一层全部条目（含 _ 开头），整轮上限 {FULL_TOTAL_TIMEOUT_SECONDS // 3600} 小时，只给定时任务",
    )
    tier.add_argument("--all", action="store_true", help="已退役，改用 --ci（CI）或 --full（定时全量）")
    tier.add_argument(
        "--id",
        dest="ids",
        nargs="+",
        action="extend",
        metavar="NAME",
        help="a 档：点名一个或多个测试，空格或逗号分隔（--id a,b,c）；可重复给，等价于 --id-<名字> 给一个",
    )
    parser.add_argument(
        "--jobs",
        type=positive_int,
        default=None,
        metavar="N",
        help=f"同时运行的测试进程数，默认 {DEFAULT_JOBS}；b 档（--ci）固定 {CI_JOBS}，不接受覆盖",
    )
    parser.add_argument("--timing", action="store_true", help="打印按耗时降序的逐项表")
    parser.add_argument(
        "--reimport", action="store_true", help="导出前强制重新导入资源（.godot 缓存过期时用）"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="导出 debug 包再在包里跑（默认用编辑器可执行文件直跑）；包里会丢内嵌节点，UI 相关条目会红",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="一批里第一个失败就停止其余测试（b/c 档与多项 --id 都适用）",
    )
    for name in tests:
        parser.add_argument(f"--id-{name}", dest=name, action="store_true", help=tests[name])
    args = parser.parse_args(argv)
    if args.all:
        print(
            "--all 已退役：提交与 CI 用 --ci（tests/ 一层非 _ 开头、固定 4 线程、无整轮上限），"
            "定时全量用 --full（含 _ 开头的条目）",
            file=sys.stderr,
        )
        return 2
    if args.ci and args.jobs is not None:
        print(f"b 档（--ci）固定 {CI_JOBS} 线程，不接受 --jobs", file=sys.stderr)
        return 2
    selected = merge_selection(args, tests)
    if (args.ci or args.full) and selected:
        print(
            "--ci / --full 不能再带 --id：要么跑一整档，要么点名一批",
            file=sys.stderr,
        )
        return 2
    unknown = [name for name in selected if name not in tests]
    if unknown:
        report_unknown_tests(unknown, tests)
        return 2
    tier_label = TIER_ID_LABEL
    names = selected or [DEFAULT_TEST]
    jobs = args.jobs or DEFAULT_JOBS
    total_timeout_seconds = None
    if args.ci or args.full:
        tier_label = TIER_CI_LABEL if args.ci else TIER_FULL_LABEL
        names = list(tests)
        jobs = CI_JOBS if args.ci else DEFAULT_JOBS
        # b 档不设整轮上限（total_timeout_seconds 保持 None）；只有 c 档有 2 小时上限。
        if args.full:
            total_timeout_seconds = FULL_TOTAL_TIMEOUT_SECONDS
        if len(names) > MAX_TESTS:
            print(
                f"{tier_label} 有 {len(names)} 个测试条目，超过上限 {MAX_TESTS}。请合并测试条目。",
                file=sys.stderr,
            )
            return 2
    if args.full:
        # 脚本分不清调用者，只能先用提示语 + 文档约束「c 档禁止开发自测」。
        print(FULL_DISABLED_HINT, file=sys.stderr)
    executable = (
        prepare_export_templates(engine_module)
        if args.export
        else quiet(engine_module.prepare_engine)
    )
    # 全新检出的 .godot 缓存是空的：先导入，再编译 C#，否则引擎起不来也解析不到 [GlobalClass]。
    if not ensure_imported(executable, args.reimport):
        return 1
    if not build_project(engine_module, executable):
        return 1
    export_directory = create_export_directory() if args.export else LOG_DIRECTORY
    concurrent = len(names) > 1
    result = run_tests(
        names,
        tests,
        export_directory,
        executable,
        concurrent=concurrent,
        jobs=jobs,
        tier_label=tier_label,
        exported=args.export,
        show_timing=args.timing,
        fail_fast=args.fail_fast,
        test_timeout_seconds=TEST_TIMEOUT_SECONDS,
        total_timeout_seconds=total_timeout_seconds,
    )
    # 先冲掉缓冲的测试结论，再做收尾检查：输出被重定向时 stdout 是块缓冲、stderr 不是，
    # 不冲的话「测试通过」会排在下面的「未提交文件 / 失效 .uid」错误之后。
    sys.stdout.flush()
    if has_uncommitted_files():
        print("错误：测试完毕后工作区存在未提交文件", file=sys.stderr)
        return 1
    invalid_sidecars = invalid_godot_sidecars()
    if invalid_sidecars:
        print("错误：发现失效的 .uid / .import 伴生文件：", file=sys.stderr)
        for path in invalid_sidecars:
            print(f"  {path}", file=sys.stderr)
        return 1
    return result


def has_uncommitted_files() -> bool:
    """工作区是否有未提交或未跟踪且未被 ignore 的文件；不是 git 仓库或没有 git 时当干净。"""
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=PROJECT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return False
    if completed.returncode != 0:
        return False
    return any(line.strip() for line in completed.stdout.splitlines())


def invalid_godot_sidecars() -> list[str]:
    """列出失效的 .uid / .import：对应源不存在，或 .import 无法解析出存在的 res:// 源。"""
    stale: list[str] = []
    for root, directories, files in os.walk(PROJECT):
        # 嵌套的独立 Godot 工程有自己的 res:// 根，按本源目录解析会误报。
        directories[:] = [
            name
            for name in directories
            if name not in SKIP_SOURCE_DIRECTORIES
            and not (Path(root) / name / "project.godot").is_file()
        ]
        for name in files:
            path = Path(root) / name
            if name.endswith(".uid"):
                if not path.with_suffix("").exists():
                    stale.append(path.relative_to(PROJECT).as_posix())
            elif name.endswith(".import"):
                source = import_source_file(path)
                if source is None or not source.exists():
                    stale.append(path.relative_to(PROJECT).as_posix())
    return sorted(stale)


def import_source_file(import_file: Path) -> Path | None:
    """把 .import 里的 source_file 解析回源资产路径；缺字段或不是 res:// 时视为失效。"""
    try:
        text = import_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        key, _, value = line.partition("=")
        if key.strip() != "source_file":
            continue
        value = value.strip().strip('"')
        if not value.startswith("res://"):
            return None
        return PROJECT / value[len("res://") :]
    return None


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("--jobs 至少是 1")
    return value


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
def isolated_user_data_environment(base_directory: Path, name: str) -> dict[str, str]:
    """每个条目一份 user:// 根：偏好、存档与夹具表互不覆盖（包模式随包删，直跑留在运行目录）。"""
    user_data_directory = base_directory / "user_data" / name
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
    exported: bool = False,
    fail_fast: bool = False,
    tier_label: str = TIER_ID_LABEL,
    test_timeout_seconds: float | None = None,
    total_timeout_seconds: float | None = None,
) -> int:
    started = time.monotonic()
    batch_deadline = started + total_timeout_seconds if total_timeout_seconds else None
    processes: list[subprocess.Popen[str]] = []
    processes_lock = threading.Lock()
    batch_timed_out = threading.Event()
    batch_timer = None
    if batch_deadline is not None:
        # 全量上限从导出前就开始算：导出卡住也要能被终止。
        batch_timer = threading.Timer(
            max(0.0, batch_deadline - time.monotonic()),
            lambda: (batch_timed_out.set(), stop_registered(processes, processes_lock)),
        )
        batch_timer.daemon = True
        batch_timer.start()

    try:
        # 默认宿主是编辑器可执行文件（项目运行模式，带 editor 特性）：导出包里内嵌在别的场景里的节点
        # （例如 ui.tscn 的 %OverviewMap）会丢，UI 相关条目全红，所以出包是可选路径。
        binary = executable
        if exported:
            binary = export_debug(
                executable, export_directory, processes, processes_lock, batch_deadline
            )
        if binary is None:
            remove_package_directory(export_directory)
            if batch_timed_out.is_set():
                print(
                    f"{tier_label} 超过 {total_timeout_seconds / 60:g} 分钟上限，已终止",
                    file=sys.stderr,
                )
                print(TIMEOUT_NOTICE, file=sys.stderr)
            print_log_tail(export_log_path())
            return 1

        cancel = threading.Event() if concurrent and fail_fast else None
        cancel_lock = threading.Lock()
        # 4 个引擎同时启动会一起去建 Vulkan swapchain，3~4G 显存的机器会随机报
        # VK_ERROR_OUT_OF_HOST_MEMORY：并发不变，只把启动时刻按 LAUNCH_SPACING_SECONDS 错开。
        launch_gate = threading.Lock()
        last_launch = [0.0]

        def wait_launch_slot() -> None:
            if not concurrent:
                return
            with launch_gate:
                delay = last_launch[0] + LAUNCH_SPACING_SECONDS - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                last_launch[0] = time.monotonic()

        def run_named(name: str) -> tuple[str, float, int, str]:
            run_directory = test_run_directory(name)
            log_path = test_log_path(name)
            if cancel is not None and cancel.is_set():
                log_path.write_text("前面的测试失败，已跳过本项\n", encoding="utf-8")
                return name, 0.0, SKIPPED_EXIT_CODE, ""
            if batch_timed_out.is_set():
                log_path.write_text(f"{tier_label} 已到时间上限，本项未跑\n", encoding="utf-8")
                return name, 0.0, TIMEOUT_EXIT_CODE, ""
            test_started = time.monotonic()
            wait_launch_slot()
            code = run_and_watch(
                launch_command(
                    binary,
                    tests[name],
                    run_directory,
                    project_mode=not exported,
                    concurrent_jobs=jobs if concurrent else 0,
                ),
                log_path,
                working_directory=run_directory,
                environment=isolated_user_data_environment(run_directory.parent, name),
                cancel=cancel,
                processes=processes,
                processes_lock=processes_lock,
                timeout_seconds=test_timeout_seconds,
                deadline=batch_deadline,
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
            if exported:
                remove_package_directory(export_directory)
    finally:
        if batch_timer is not None:
            batch_timer.cancel()

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
    if batch_timed_out.is_set():
        print(
            f"{tier_label} 超过 {total_timeout_seconds / 60:g} 分钟上限，已终止；本轮结果不作通过依据",
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
    # 全部通过：只报结论与总耗时，过程输出都在 .export/.test_<GUID>/ 里。
    print("测试通过")
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


def launch_command(
    binary: Path,
    scene: str,
    run_directory: Path,
    project_mode: bool = False,
    concurrent_jobs: int = 0,
) -> list[str]:
    command = [str(binary), "--audio-driver", "Dummy"]
    if project_mode:
        # 编辑器可执行文件以项目运行模式直跑脚本：不开编辑器界面、不导出包。
        command.extend(["--path", str(PROJECT)])
    if sys.platform.startswith("linux") and not project_mode:
        command.extend(["--display-driver", "headless"])
    command.extend(
        [
            "--",
            f"--test={scene}",
            f"--run-directory={run_directory}",
        ]
    )
    if concurrent_jobs > 1:
        # 并发跑时墙钟里混着排队：帧预算类断言据此放宽到并发档（见 tests/.readme.txt）。
        command.append(f"--concurrent={concurrent_jobs}")
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
