#!/usr/bin/env python3
"""按 project.godot 的 [engine_host] 准备 Godot。无参数时打开编辑器，有参数时把参数交给引擎并等待结束。"""

from __future__ import annotations

import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "project.godot"

# 标准构建与 .NET（mono）构建的引擎包不同：dotnet="true" 时下 mono 包，
# 装进带 -dotnet 后缀的目录，与标准引擎并存。
STANDARD_HOST_PACKAGES = {
    "windows": {
        "slug": "win64.exe.zip",
        "download_platform": "windows.64",
        "executable_name": "Godot_v{version}-{flavor}_win64.exe",
    },
    "linux": {
        "slug": "linux.x86_64.zip",
        "download_platform": "linux.64",
        "executable_name": "Godot_v{version}-{flavor}_linux.x86_64",
    },
    "darwin": {
        # Godot 4.8 起 macOS 构建按架构拆包，universal 已不再提供（下载 API 对
        # macos.universal.zip 回 404）。slug 里留占位，由 host_package() 按本机架构填。
        "slug": "macos.{architecture}.zip",
        "download_platform": "osx.universal",
        "executable_name": "Godot.app/Contents/MacOS/Godot",
    },
}

DOTNET_HOST_PACKAGES = {
    "windows": {
        "slug": "mono_win64.zip",
        "download_platform": "windows.64",
        "executable_name": "Godot_v{version}-{flavor}_mono_win64.exe",
    },
    "linux": {
        "slug": "mono_linux.x86_64.zip",
        "download_platform": "linux.64",
        "executable_name": "Godot_v{version}-{flavor}_mono_linux.x86_64",
    },
    "darwin": {
        # .NET 构建同样按架构拆包，mono_macos.universal.zip 已回 404。
        "slug": "mono_macos.{architecture}.zip",
        "download_platform": "osx.universal",
        "executable_name": "Godot.app/Contents/MacOS/Godot",
    },
}


ENGINE_CONFIG_DEFAULTS = {
    "version": "4.8",
    "flavor": "beta2",
    "install_directory": "~/godots",
    "dotnet": "false",
}

# 转交参数时逐行看引擎输出，命中这些前缀就停掉引擎并判失败；警告只转发不停。
OFFENDING_PREFIXES = (
    "SCRIPT ERROR:",
    "ERROR:",
    "USER ERROR:",
)


def read_config_section(
    section: str,
    defaults: dict[str, str] | None = None,
    config_path: Path = CONFIG_PATH,
) -> dict[str, str]:
    """读 project.godot 的一个 [section]，缺字段回退到 defaults。"""
    values = dict(defaults or {})
    in_section = False
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            in_section = line[1:-1].strip() == section
            continue
        if not in_section:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_engine_config(config_path: Path = CONFIG_PATH) -> dict[str, str]:
    """缺 version / flavor / install_directory / dotnet 时用内置默认值。"""
    return read_config_section("engine_host", ENGINE_CONFIG_DEFAULTS, config_path)


def uses_dotnet(config: dict[str, str] | None = None) -> bool:
    """[engine_host] dotnet="true" 表示项目用 C#/.NET：引擎、导出模板都取 mono 版。"""
    loaded = config or load_engine_config()
    return loaded.get("dotnet", "false").strip().lower() in ("true", "1", "yes")


def host_kind() -> str:
    system_name = platform.system().lower()
    if system_name.startswith("win"):
        return "windows"
    if system_name == "linux":
        return "linux"
    if system_name == "darwin":
        return "darwin"
    raise RuntimeError(f"不支持的系统：{platform.system()}")


def macos_architecture() -> str:
    machine = platform.machine().lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    raise RuntimeError(f"不支持的 macOS 架构：{platform.machine()}")


def host_package(config: dict[str, str] | None = None) -> dict[str, str]:
    loaded = config or load_engine_config()
    packages = DOTNET_HOST_PACKAGES if uses_dotnet(loaded) else STANDARD_HOST_PACKAGES
    package = dict(packages[host_kind()])
    if host_kind() == "darwin":
        package["slug"] = package["slug"].format(architecture=macos_architecture())
    return package


def engine_directory(config: dict[str, str] | None = None) -> Path:
    loaded = config or load_engine_config()
    install_text = loaded["install_directory"]
    if install_text.startswith("~") or Path(install_text).is_absolute():
        install_directory = Path(install_text).expanduser()
    else:
        install_directory = ROOT / install_text
    edition_suffix = "-dotnet" if uses_dotnet(loaded) else ""
    return install_directory / f"{loaded['version']}-{loaded['flavor']}{edition_suffix}"


def engine_executable(config: dict[str, str] | None = None) -> Path:
    loaded = config or load_engine_config()
    package = host_package(loaded)
    file_name = package["executable_name"].format(
        version=loaded["version"],
        flavor=loaded["flavor"],
    )
    return engine_directory(loaded) / file_name


def prepare_engine() -> Path:
    executable = engine_executable()
    marker = executable.parent / "._sc_"
    if marker.is_file():
        marker.unlink()
    if executable.is_file():
        print(f"引擎已存在，跳过下载：{executable}", file=sys.stderr)
        return executable
    config = load_engine_config()
    package = host_package(config)
    # 解压到版本目录而不是可执行文件所在目录：macOS 的可执行文件在
    # Godot.app/Contents/MacOS/ 里，解压到那里会把整个 .app 再套一层。
    destination = engine_directory(config)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    archive_path = destination / "godot.zip"
    download_url = (
        "https://downloads.godotengine.org/"
        f"?version={config['version']}&flavor={config['flavor']}"
        f"&slug={package['slug']}&platform={package['download_platform']}"
    )
    edition_label = "dotnet" if uses_dotnet(config) else "standard"
    print(
        f"下载 {config['version']}-{config['flavor']} ({edition_label})：{download_url}",
        file=sys.stderr,
    )
    request = urllib.request.Request(download_url, headers={"User-Agent": "godot-best-practice"})
    with urllib.request.urlopen(request) as response, archive_path.open("wb") as archive_file:
        shutil.copyfileobj(response, archive_file)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(destination)
    archive_path.unlink()
    if not executable.is_file():
        found = next(destination.rglob(executable.name), None)
        if found is None:
            raise RuntimeError(f"压缩包里没有 {executable.name}")
        if found.parent != destination:
            for child in found.parent.iterdir():
                shutil.move(str(child), destination / child.name)
            leftover = found.parent
            if leftover != destination and not any(leftover.iterdir()):
                leftover.rmdir()
    if not executable.is_file():
        raise RuntimeError(f"引擎可执行文件不存在：{executable}")
    if host_kind() != "windows":
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"引擎准备完成：{executable}", file=sys.stderr)
    return executable


def hide_double_click_console() -> None:
    """Windows 双击 .py 时控制台只挂着自己，隐藏它；终端里共享的控制台不动。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        window = kernel32.GetConsoleWindow()
        if not window:
            return
        attached = (ctypes.c_uint * 2)()
        if kernel32.GetConsoleProcessList(attached, len(attached)) != 1:
            return
        ctypes.windll.user32.ShowWindow(window, 0)
    except Exception:
        pass


def stop_engine(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
        )
    else:
        process.kill()


def run_engine(executable: Path, argv: list[str]) -> int:
    """前台跑引擎并转发输出：见错误就停掉引擎、打印出来并返回 1。"""
    process = subprocess.Popen(
        [str(executable), *argv],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    offending = False
    assert process.stdout is not None
    try:
        for raw_line in process.stdout:
            sys.stdout.write(raw_line)
            sys.stdout.flush()
            line = raw_line.strip()
            if any(line.startswith(prefix) for prefix in OFFENDING_PREFIXES):
                offending = True
                stop_engine(process)
                print(f"发现错误，已停止引擎：{line}", file=sys.stderr)
                break
    finally:
        process.wait()
    return 1 if offending else process.returncode


def main(argv: list[str]) -> int:
    hide_double_click_console()
    try:
        executable = prepare_engine()
        if not argv:
            arguments = [str(executable), "--editor", "--path", str(ROOT)]
            if sys.platform == "win32":
                process = subprocess.Popen(
                    arguments,
                    cwd=ROOT,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
            else:
                process = subprocess.Popen(
                    arguments,
                    cwd=ROOT,
                    start_new_session=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            print(f"引擎进程 PID：{process.pid}")
            return 0
        if argv[:1] == ["--"]:
            argv = argv[1:]
        return run_engine(executable, argv)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
