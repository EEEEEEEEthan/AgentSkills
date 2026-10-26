# 引擎安装

Godot 不进仓库。版本和安装位置写在仓库根的 `.engine-config.toml`。这是 TOML，和 Codex 的 `config.toml` 同一类格式。

```toml
version = "4.7.2"
flavor = "stable"
install_directory = "~/godot"
```

`install_directory` 以 `~` 或绝对路径开头时按用户路径展开，实际目录是 `{install_directory}/{version}-{flavor}/`。其它写法相对仓库根，例如 `.cache/godot`。

## 启动

`.engine` 自己下载。不用先跑准备脚本。

Windows：

```bat
.engine.bat
.engine.bat --headless --path . --quit
```

Linux，以及装了 bash 的 macOS：

```bash
./.engine.sh
./.engine.sh --headless --path . --quit
```

不带参数时打开编辑器。后面的参数原样交给 Godot。引擎不在配置目录里时会从 `downloads.godotengine.org` 下载。

macOS 能下载并打开编辑器。

## 拷进项目

把本技能的 `project-template/` 拷到仓库根。目标里已经有的文件不要覆盖。

拷进去之后直接：

```text
python .test_entry.py --smoke
```

`.test_entry.py` 通过旁边的 `.engine.bat` / `.engine.sh` 调引擎。冒烟是 `tests/smoke.gd`，游戏进程起来即通过。`project.godot` 可以先是空的；跑测试时会补上 Autoload `TestEntry="*res://tests/test_entry.gd"`，Godot 已经写过的配置保留。专项再加进 `TESTS`。见 [testing.md](testing.md)。
