# 引擎安装

Godot 不进仓库。版本和安装位置写在 `project.godot` 的 `[engine_host]`。测试入口写在同一文件的 `[autoload]`。

```ini
[autoload]

TestEntry="*res://tests/_test_entry.gd"

[engine_host]

version="4.7.2"
flavor="stable"
install_directory="~/godot"
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
python .engine_test.py
```

`.engine_test.py` 通过旁边的 `.engine.bat` / `.engine.sh` 调引擎。不带参数跑 `tests/smoke.gd`，游戏进程起来即通过。`--all` 并发跑 `tests` 目录下一层、不以 `_` 开头的 gd。见 [testing.md](testing.md)。
