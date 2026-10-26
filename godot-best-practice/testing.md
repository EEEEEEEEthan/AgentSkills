# Godot 自动化测试最佳实践

冒烟唯一、专项可复用、时限写在测试代码里、由 Python 出 debug 包再跑。

## 两层

- **冒烟**：唯一。覆盖大部分游戏流程，不是全部。CI 只跑这一条。
- **专项**：很多条，每条覆盖完整 case。开发结束自测时跑。冒烟直接调用其中的某个或某些方法，不把流程再写一遍。

每个测试脚本都 `extends Node`，冒烟和专项一样。不要为测试建 `.tscn`。

## 时间上限

冒烟和专项的入口都在测试代码里写死时间上限。超时即失败。上限取恰好能通过的最短时间。

## 断言

测玩法结果。不规定控件尺寸这类无关细节，除非该尺寸本身就是要验收的行为。

## 启动

Godot 捕获不了脚本报错，编辑器运行和真包也不一致。测试由一个 Python 脚本启动。它调用项目里的 `.engine.bat` / `.engine.sh`（见 [setup.md](setup.md)），不写死本机 Godot 路径。版本和安装目录在 `project.godot` 的 `[engine_host]`。测试入口 Autoload 也写在这个文件里。冒烟和专项都是它的一个选项，一次只跑一个：

```text
python .engine_test.py
python .engine_test.py --smoke
python .engine_test.py --monkey
```

不带参数就是冒烟。`--smoke` 也是这一条。专项的选项名就是测试名，例如专项叫 monkey 就是 `--monkey`。CI 只跑冒烟。

顺序固定：

1. 把 debug 包导出到临时目录下的 GUID 子目录，避免并发写到同一路径。导出时引擎会自己导入资源。
2. 用该包跑对应的 GDScript，不在编辑器里跑。
3. 转发 Godot 的 stdout / stderr，供看日志。
4. 输出里一出现错误或警告就立刻停，不等测试自己退出，也不等超时。

`TESTS` 的值是 `res://tests/.../*.gd`。导出包不接受编辑器的场景路径。Autoload `tests/test_entry.gd` 读 `--test=`，脚本必须 `extends Node`，`load` 后 `new()`，挂到自己下面。不要 `set_script()`。

模板在 [project-template/.engine_test.py](project-template/.engine_test.py)，和 `.engine.bat` / `.engine.sh` 一起在安装时拷进仓库。它只通过这两个脚本启动引擎。初始冒烟是 [project-template/tests/smoke.gd](project-template/tests/smoke.gd)。专项加进 `TESTS`。
