#!/usr/bin/env python3
"""按 .engine-config.toml 下载 Godot，并返回或启动对应平台的可执行文件。"""

from __future__ import annotations

import argparse
import platform
import shutil
import stat
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / ".engine-config.toml"

HOST_PACKAGES = {
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
        "slug": "macos.universal.zip",
        "download_platform": "osx.universal",
        "executable_name": "Godot.app/Contents/MacOS/Godot",
    },
}


def load_engine_config(config_path: Path = CONFIG_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    missing = [key for key in ("version", "flavor", "install_directory") if key not in values]
    if missing:
        raise RuntimeError(f"{config_path} 缺少 {', '.join(missing)}")
    return values


def host_kind() -> str:
    system_name = platform.system().lower()
    if system_name.startswith("win"):
        return "windows"
    if system_name == "linux":
        return "linux"
    if system_name == "darwin":
        return "darwin"
    raise RuntimeError(f"不支持的系统：{platform.system()}")


def engine_directory(config: dict[str, str] | None = None) -> Path:
    loaded = config or load_engine_config()
    install_text = loaded["install_directory"]
    if install_text.startswith("~") or Path(install_text).is_absolute():
        install_directory = Path(install_text).expanduser()
    else:
        install_directory = ROOT / install_text
    return install_directory / f"{loaded['version']}-{loaded['flavor']}"


def engine_executable(config: dict[str, str] | None = None) -> Path:
    loaded = config or load_engine_config()
    package = HOST_PACKAGES[host_kind()]
    file_name = package["executable_name"].format(
        version=loaded["version"],
        flavor=loaded["flavor"],
    )
    return engine_directory(loaded) / file_name


def prepare_engine() -> Path:
    executable = engine_executable()
    if executable.is_file():
        print(f"引擎已存在，跳过下载：{executable}", file=sys.stderr)
        return executable
    config = load_engine_config()
    package = HOST_PACKAGES[host_kind()]
    destination = executable.parent
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    archive_path = destination / "godot.zip"
    download_url = (
        "https://downloads.godotengine.org/"
        f"?version={config['version']}&flavor={config['flavor']}"
        f"&slug={package['slug']}&platform={package['download_platform']}"
    )
    print(f"下载 {config['version']}-{config['flavor']}：{download_url}", file=sys.stderr)
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


def run_engine(arguments: list[str]) -> int:
    import subprocess

    executable = prepare_engine()
    completed = subprocess.run([str(executable), *arguments], cwd=ROOT)
    return completed.returncode


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="下载配置里的引擎版本")
    subparsers.add_parser("path", help="打印引擎可执行文件路径，必要时先下载")
    run_parser = subparsers.add_parser("run", help="准备引擎后把参数转交给它")
    run_parser.add_argument("engine_arguments", nargs=argparse.REMAINDER)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "prepare":
            prepare_engine()
            return 0
        if arguments.command == "path":
            print(prepare_engine())
            return 0
        engine_arguments = arguments.engine_arguments
        if engine_arguments[:1] == ["--"]:
            engine_arguments = engine_arguments[1:]
        return run_engine(engine_arguments)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
