# Godot 自动化测试最佳实践

每条测试都是 `tests` 目录下一层的 `extends Node` 脚本，文件名不以 `_` 开头。`_test_entry.gd` 是入口，不参与测试。不带参数时跑 `smoke`。CI 跑 `--all`。不要为测试建 `.tscn`。不要递归子目录。

`tests` 一层一个文件就是 `--all` 的一条「大条目」，条目里的用例脚本放 `tests/cases/`，在条目的 `CASES` 里登记，由 `_run_cases()` 在同一个进程里依次跑（省掉每条一次引擎启动）。一条用例红，整条条目红。`--case=<用例名>` 能单跑一条用例，但必须同时 `--id` 点名一个条目。

条目数量有上限（`max_tests`），加用例优先往已有条目里加，不要为每条用例新建条目。同一进程跑多条用例要自己清场：`_reset_between_cases()` 只管窗口尺寸、设置文件、存档目录与待启动的局，用例自己改过的全局状态要在结束前还原。上一用例留在树上的场景会让下一用例的点击落空——这种情况先调 `CASES` 顺序，不要改断言。

## 时间上限

时间上限统一由 `.engine_test.py` 管，测试脚本不再自己写。单项默认 1 分钟，`--all` 全量默认 5 分钟（含导出）；上限在 `project.godot` 的 `[test]` 里配置。到点由脚本直接强杀进程，没有跳过、延长或关闭超时的参数。单项与全量超时都打印同一句原文：

```text
测试超时，请精简测试项。禁止修改测试用时。
```

一项要跑得久，先删/缩这个条目里最贵的用例，再降自己推进仿真的步长与人口规模；不要靠加并发或放松上限。测性能的断言（「N 个 X 跑 M 帧不超过 T 毫秒」）上限要留足机器繁忙时的噪声余量，只当灾难性退化的警报。

## 逐项耗时与均衡

每个测试进程结束记一行 `<测试名> 用时 <秒，两位小数> 退出码 <码>` 到 `.export/.test_<GUID>/timings.csv`：`seconds` 是整个测试进程的墙钟，`boot_ms` 是 `_test_entry.gd` 挂测试节点前的启动段（引擎 + autoload + 主场景），两者相减是用例本体。

全部通过时终端只打印总耗时 `总计 <秒>s`，`--timing` 另外打一张按耗时降序的逐项表。失败时才打印错误、失败项的日志路径与日志尾部；模板下载、导入、编译、导出与逐项成功的过程输出都不往终端打。

一批里实际跑完的项（跳过与超时的不计）如果 `max - min > max * 0.5`，`--timing` 会提示：

```text
请合理规划测试项，使每个测试项耗时尽可能相同，以充分发挥并发优势
```

看到就拆细最长的条目，或把用例挪到短的条目里。并发收益由最慢的一项决定，耗时差太大等于白并发。


## 断言

测玩法结果。不规定控件尺寸这类无关细节，除非该尺寸本身就是要验收的行为。

跟帧数有关的断言（「下一帧就该看得见」）在并发跑时不可靠：写成轮询到条件成立或超时。

测试里没有真鼠标，视口光标固定在 `(0,0)`（屏幕角落）。凡是自己 `load` 主场景再往地图上点选、拖拽的用例，都要把 `%IsometricCamera` 的 `edge_scroll_enabled` 关掉，否则相机一直往角上滚，点选与拖拽起点会落偏。

## 启动

Godot 捕获不了脚本报错，编辑器运行和真包也不一致。测试由一个 Python 脚本启动。它用项目里的 `.engine.py`（见 [setup.md](setup.md)）定位并下载引擎，不写死本机 Godot 路径；导入、构建、导出与跑测试都直接调用引擎可执行文件。版本和安装目录在 `project.godot` 的 `[engine_host]`，缺字段时用默认 `4.8` / `beta2` / `~/godots`。测试入口 Autoload 也写在这个文件里。

```text
python .engine_test.py
python .engine_test.py --id-smoke
python .engine_test.py --id smoke road_network
python .engine_test.py --all
```

不写参数就是 `smoke`。`--id` 点名一个或多个测试，空格分隔，也可重复给；`--id-<名字>` 等价于点一项。点名一项时前台串行；点名多项或 `--all` 时并发，失败不中断其余项（要第一项失败就停加 `--fail-fast`）。全部成功才结束；失败项最后逐条列出，并打印各自的日志尾部。

并发、条目上限与时间上限在 `project.godot` 的 `[test]` 配置，缺字段时用默认值：

- `max_tests=32`：`--all` 的条目上限，超过直接报错，先把测试脚本合并。
- `test_timeout_minutes=1`：单项上限，超时终止并报错。
- `total_timeout_minutes=5`：`--all` 全量上限（含导出），超时终止并报错。
- `jobs=4`：并发数，`--jobs` 可临时覆盖。8 核 8G 的机器上再往上加会把单项墙钟抬到 2~3 倍。

跑完后还会检查 `git status`：有未提交或未跟踪且未被 ignore 的文件就报错。测试产物放在 `.export/`，模板 `.gitignore` 已忽略它。

开跑前还会查被跟踪的 `*.uid` 与 `*.import`：源文件已经不在了的元数据直接报错并一次列出全部路径。Godot 删除脚本或资源时不会回收同名元数据，留着会让编辑器导入报出幽灵路径，删源文件时要连元数据一起删。与 `git status` 一样，不是 git 仓库时跳过。

引擎放在 `install_directory`。`.engine_test.py` 在导出前检查 Godot 用户目录里的 `export_templates/<版本>/version.txt`。Linux 是 `$XDG_DATA_HOME/godot`，没设置 `XDG_DATA_HOME` 时是 `~/.local/share/godot`（小写 `godot`）。Windows 是 `%APPDATA%\Godot`。没有 `version.txt` 则下载 `export_templates.tpz` 并解压到那里；`[engine_host] dotnet="true"` 时改下 `mono_export_templates.tpz`。不要写成 `~/.local/share/Godot`，当前引擎不会去那里找 `linux_debug.x86_64`。初始化工程时不下载导出模板。

顺序固定：

1. 准备导出模板：没有 `version.txt` 时下载到 Godot 用户目录（Linux 为 `~/.local/share/godot/export_templates/<版本>/`，Windows 为 `%APPDATA%\Godot\export_templates\<版本>/`）。
2. dotnet 工程先 `--build-solutions` 编译 C# 解决方案，全新检出不构建就解析不到 C# 的 `[GlobalClass]`。
3. 导入资源：`.godot/imported` 为空（全新检出、新 worktree）或给了 `--reimport` 时，先跑一次 `--import`。导出只认已有的导入产物，引擎不会自己导入；导入失败直接退出 1，不带着空缓存去导出。冷缓存时不要并跑两路 `--all`，它们会同时写同一份 `.godot`。
4. 导出 debug 包到 `.export/test/`，产物按项目名命名，各项测试共用；导出输出写 `.export/.test_<GUID>/export.log`，成功不打印，失败打印尾部。每次运行另建 `.export/.test_<GUID>/` 存日志与运行目录。
5. 用该包跑对应的 GDScript，不在编辑器里跑。Linux 加 `--display-driver headless`，所有平台加 `--audio-driver Dummy`，避免显卡和声卡的驱动警告把测试停掉。每项的运行目录是 `.test_<GUID>/<测试名>/`，日志是同目录的 `<测试名>.log`，`user://` 落在包目录的 `user_data/<测试名>/`，并发时各进程互不覆盖。
6. Godot 的 stdout / stderr 写进 `<测试名>.log`；成功不打印，失败时打印日志尾部。
7. 测试进程输出里一出现错误或警告就立刻停，不等测试自己退出，也不等超时。导出阶段例外：只认退出码与产物。
8. 测完删掉整个 `.export/test/` 与 `user_data`，只留 `.test_<GUID>/` 下的日志、运行目录和 `timings.csv`。


`tests` 目录下一层、不以 `_` 开头的 gd 都会被 `--all` 纳入。导出包不接受编辑器的场景路径。Autoload `tests/_test_entry.gd` 读 `--test=`，脚本必须 `extends Node`，`load` 后 `new()`，挂到自己下面。不要 `set_script()`。

## 存档

editor 和 debug 包的存档放在这次的运行目录下，避免并发写到同一处。release 包再用别的位置，例如用户目录。

模板在 [project-template/.engine_test.py](project-template/.engine_test.py)，和 `.engine.py` 一起在安装时拷进仓库。它用 `.engine.py` 定位并下载引擎，导入、构建、导出与跑测试都直接调引擎可执行文件；导出阶段只认退出码与产物，引擎为着色器/资源打的 ERROR 不算导出失败。默认测试是 [project-template/tests/smoke.gd](project-template/tests/smoke.gd)。其它测试放在 `tests` 目录下一层。
