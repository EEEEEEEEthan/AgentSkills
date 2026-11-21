# Godot 自动化测试最佳实践

## 三档

`.engine_test.py` 把测试分三档，条目上限、并发与时间上限全部写死在脚本里（常量 `MAX_TESTS` / `DEFAULT_JOBS` / `CI_JOBS` / `TEST_TIMEOUT_SECONDS` / `FULL_TOTAL_TIMEOUT_SECONDS`），**不再从 `project.godot` 读任何测试配置**。

| 档 | 命令 | 扫描范围 | 并发 | 单项上限 | 整轮上限 | 用途 |
| --- | --- | --- | --- | --- | --- | --- |
| a 点名自测 | `--id <条目>...`（空格或逗号分隔，不给参数即 `smoke`） | 点名的条目 | 4，`--jobs` 可改 | 30 分钟 | 无 | 每轮开发后的自测 |
| b CI | `--ci` | `tests/` 一层、文件名不以 `_` 开头 | 限死 4，给 `--jobs` 直接退出 2 | 30 分钟 | 无 | 提交 / MR / CI |
| c 全量 | `--full` | `tests/` 一层全部（含 `_` 开头的条目） | 4 | 30 分钟 | 2 小时 | 只给定时任务 |

- 开发自测只到 a / b 两档；**c 档禁止开发自测**，留给每天一次的定时任务（脚本开跑时会往 stderr 打一行提示）。
- 三个选择互斥：`--ci` / `--full` / `--id` 不能同时给。
- `--all` 已退役，见到直接退出 2 并指向 `--ci` / `--full`。
- `--case=<用例名>` 也退出了 CLI：单跑一条用例直接跑引擎，见下面的「启动」。

## 目录约定

- `tests/*.gd`：一层一个「大条目」，只有这一层算条目；首个非注释行必须是 `extends TestScriptBase`，否则会被跳过（stderr 报一行「跳过非测试脚本」）。
- `tests/cases/*.gd`：条目里的用例脚本，一条用例一个文件，不会自己进任何档，由条目的 `CASES` 登记。
- `tests/tools/`：工具、夹具、预览（`_*_preview.gd` / `_*.tscn`）、测试基座 `_test_script_base.gd`、建筑验收辅助脚本与 `_test_entry.gd`（Autoload 入口）全放这里。**该目录任何档都不扫**。
- 别为测试建 `.tscn`，也不要让条目递归子目录。
- 条目一旦被 `_` 前缀挡在 b 档之外（超预算、断言已知红），它仍会被 c 档跑到；提交信息里要列出暂退 CI 的条目。

## 条目与用例

条目里的用例由 `_run_cases()` 在同一个进程里依次跑（省掉每条一次引擎启动）。一条用例红，整条条目红，日志里最后一条 `SUITE_CASE` 就是出问题的那条。加用例优先往已有条目里加，加条目才在 `tests` 一层新建文件；条目数超过 `MAX_TESTS` 直接报错。

同一进程跑多条用例要自己清场：`_reset_between_cases()` 只管窗口尺寸、设置文件、存档目录与待启动的局，用例自己改过的全局状态要在结束前还原。上一用例留在树上的场景会让下一用例的点击落空——这种情况先调 `CASES` 顺序，不要改断言。

## 时间上限

时间上限统一由 `.engine_test.py` 管，测试脚本不再自己写。单项 30 分钟，b 档不设整轮上限，c 档整轮 2 小时。到点由脚本直接强杀进程，没有跳过、延长或关闭超时的参数。单项与整轮超时都打印同一句原文：

```text
测试超时，请精简测试项。禁止修改测试用时。
```

一项要跑得久，先删/缩这个条目里最贵的用例，再降自己推进仿真的步长与人口规模；不要靠加并发或放松上限。测性能的断言（「N 个 X 跑 M 帧不超过 T 毫秒」）上限要留足机器繁忙时的噪声余量，只当灾难性退化的警报。

## 逐项耗时与均衡

每个测试进程结束记一行到 `.export/.test_<GUID>/timings.csv`（`name,seconds,code,boot_ms`）：`seconds` 是整个测试进程的墙钟，`boot_ms` 是 `_test_entry.gd` 挂测试节点前的启动段（引擎 + autoload + 主场景），两者相减是用例本体。

全部通过时终端先打印 `测试通过`，再打总耗时 `总计 <秒>s`，`--timing` 另外打一张按耗时降序的逐项表。失败时才打印错误、失败项的日志路径与日志尾部；模板下载、导入、编译、导出与逐项成功的过程输出都不往终端打。

一批里实际跑完的项（跳过与超时的不计）如果 `max - min > max * 0.5`，`--timing` 会提示：

```text
请合理规划测试项，使每个测试项耗时尽可能相同，以充分发挥并发优势
```

看到就拆细最长的条目，或把用例挪到短的条目里。并发收益由最慢的一项决定，耗时差太大等于白并发。

## 断言

测玩法结果。不规定控件尺寸这类无关细节，除非该尺寸本身就是要验收的行为。

**游戏代码里多写 `assert`，少写测试专用代码。** 测试代码只负责预设测试环境与推进游戏进程；结果对不对尽量交给游戏代码自己的断言。断言跟实现放在一起，改实现时一起改，不用让测试隔着接口去抠内部状态。

C# 的断言用宏包起来，只在 editor / debug 包启用，release 包整句剥掉：

```csharp
[Conditional("DEBUG")]
public static void IsTrue(bool condition)
{
    if (!condition) throw new InvalidOperationException();
}
```

调用固定成一条条件：

```csharp
Assert.IsTrue(a > b);
```

不要加第二个参数（错误信息、格式化参数）：断言在热路径上高频调用，多传参数拼字符串会直接吃掉性能。要写清背景就近加注释。

断言本身影响到性能，或者一条简单断言已经表达不了测试需求时，才把这段检查放进专用测试代码。

只做**关系断言**：`a + b == c`、调过 `func()` 之后 `a == $CONST`、同一函数换参数的两次读数互印证、表与资产两端对得上。没有前提的 `a == $CONST`、`size() == 6`、逐行文案比对、布局坐标比对、图元数比对都是静态对比，数据改了测试跟着改，等于没守东西；外观交给预览脚本人工看。

跟帧数有关的断言（「下一帧就该看得见」）在并发跑时不可靠：写成轮询到条件成立或超时。并发跑时脚本会给每个测试进程传 `--concurrent=<并发路数>`，性能断言据此把上限放宽到并发档（单跑严判）；并发跑的真实判据交给与机器快慢无关的计数器。

测试里没有真鼠标，视口光标固定在 `(0,0)`（屏幕角落）。凡是自己 `load` 主场景再往地图上点选、拖拽的用例，都要把 `%IsometricCamera` 的 `edge_scroll_enabled` 关掉，否则相机一直往角上滚，点选与拖拽起点会落偏。

## 启动

Godot 捕获不了脚本报错，编辑器运行和真包也不一致。测试由一个 Python 脚本启动。它用项目里的 `.engine.py`（见 [setup.md](setup.md)）定位并下载引擎，不写死本机 Godot 路径；导入、构建、导出与跑测试都直接调用引擎可执行文件。版本和安装目录在 `project.godot` 的 `[engine_host]`，缺字段时用默认 `4.8` / `beta2` / `~/godots`。测试入口 Autoload 也写在这个文件里。

```text
python .engine_test.py                      # a 档：等价 --id smoke
python .engine_test.py --id-smoke           # --id-<名字> 等价于点它一项
python .engine_test.py --id smoke walkers   # 点名一批，多项并发
python .engine_test.py --id smoke,walkers   # 逗号分隔，等价于上面一行
python .engine_test.py --ci                 # b 档：提交 / MR / CI
python .engine_test.py --full               # c 档：只给定时任务
```

不写参数就是 `smoke`。`--id` 点名一个或多个测试，名字用空格或逗号分隔，也可重复给；点名一项时前台串行，点名多项时同样并发、同样受 `--jobs` 并发上限约束、同样无总时长上限，失败不中断其余项（要第一项失败就停加 `--fail-fast`）。全部成功才结束；失败项最后逐条列出，并打印各自的日志尾部。

单跑一条用例（不经过条目）：

```bash
python .engine.py --path . -- --test=res://tests/_world.gd --case=terrain_view
```

## 宿主

默认宿主是编辑器可执行文件以项目运行模式直跑（带 `editor` 特性，不出包）；加 `--export` 才导出 debug 包再在包里跑。出包路径只作诊断：实测导出包里内嵌在别的场景实例里的节点（例如 `ui.tscn` 的 `%OverviewMap`）会整个丢，UI 相关条目全红。`_test_entry.gd` 在 `test` 或 `editor` 任一特性下放行；没有 `--test=` 的普通运行（F5 / 正式包）立刻 return。

顺序固定：

1. dotnet 工程先 `--build-solutions` 编译 C# 解决方案，全新检出不构建就解析不到 C# 的 `[GlobalClass]`。
2. 导入资源：`.godot/imported` 为空（全新检出、新 worktree）或给了 `--reimport` 时，先跑一次 `--import`。引擎只认已有的导入产物；导入失败直接退出 1，不带着空缓存去跑。冷缓存时不要并跑两路 b 档，它们会同时写同一份 `.godot`。
3. `--export` 时准备导出模板（Godot 用户目录 `export_templates/<版本>/version.txt`；Linux 是 `$XDG_DATA_HOME/godot`，Windows 是 `%APPDATA%\Godot`；`[engine_host] dotnet="true"` 时下 `mono_export_templates.tpz`）并导出 debug 包，预设按平台选 `Windows Desktop Test` / `macOS Desktop Test` / `Linux Desktop Test`。导出阶段只看退出码与产物，引擎为着色器/资源打的 ERROR 不算导出失败。
4. 用引擎跑对应的 GDScript，不在编辑器界面里跑。Linux 出包模式加 `--display-driver headless`，所有平台加 `--audio-driver Dummy`，避免显卡和声卡的驱动警告把测试停掉。每项的运行目录是 `.test_<GUID>/<测试名>/`，日志是同目录的 `<测试名>.log`，`user://` 落在 `user_data/<测试名>/`，并发时各进程互不覆盖。
5. 引擎的 stdout / stderr 写进 `<测试名>.log`；成功不打印，失败时打印日志尾部。一出现错误或警告就立刻停，不等测试自己退出，也不等超时。
6. 跑完删掉包目录（出包模式），只留 `.test_<GUID>/` 下的日志、运行目录和 `timings.csv`。
7. 跑完检查 `git status`：有未提交或未跟踪且未被 ignore 的文件就报错。测试产物放 `.export/`，模板 `.gitignore` 已忽略它。工作区干净后再查失效的 `.uid` / `.import` 伴生文件（源已删的 `.uid`、源不存在或无法解析的 `.import`）：全部列出并退出 1；按 `res://` 解析，嵌套的独立 Godot 工程不参与。

并发跑时相邻测试进程的启动错开 2 秒（`LAUNCH_SPACING_SECONDS`）：同时启动的多个引擎会一起去建 Vulkan swapchain，显存吃紧的机器（实测 3G 的 GTX 1060 连 2 路并发都会撞）会随机报 `VK_ERROR_OUT_OF_HOST_MEMORY` 而判红。b 档的 4 线程要在显存 ≥6G 的机器上跑；这是机器容量问题，不是用例回归，也不要用降并发或复跑掩盖。

Autoload `tests/tools/_test_entry.gd` 读 `--test=`，脚本必须 `extends Node`，`load` 后 `new()`，挂到自己下面。不要 `set_script()`。导出包不接受编辑器的场景路径。

## 每天定时跑 c 档

c 档是「整轮 2 小时」的全量档，只在定时任务里跑：

```text
python .engine_test.py --full
```

放进项目的定时任务（Hub 的周期任务、cron 或夜间 CI 均可，建议每天一次、避开提交高峰），开发过程中不跑它。定时任务失败就看 `.export/.test_<GUID>/` 下的日志与 `timings.csv`；要复现某一项，用 a 档点名那一条，别再用 c 档。

## 存档

editor 和 debug 包的存档放在这次的运行目录下，避免并发写到同一处。release 包再用别的位置，例如用户目录。

模板在 [project-template/.engine_test.py](project-template/.engine_test.py)，和 `.engine.py` 一起在安装时拷进仓库。默认测试是 [project-template/tests/smoke.gd](project-template/tests/smoke.gd)（只验进程起得来）。其它测试放在 `tests` 目录下一层，工具脚本放 `tests/tools/`。
