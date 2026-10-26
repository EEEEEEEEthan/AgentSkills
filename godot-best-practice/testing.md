# Godot 自动化测试最佳实践

每条测试都是一个 `extends Node` 的 GDScript，走同一条启动路径。不带参数时跑 `smoke`。CI 跑这一条。不要为测试建 `.tscn`。

## 时间上限

每条测试的入口自己写死时间上限。超时即失败。上限取恰好能通过的最短时间。

## 断言

测玩法结果。不规定控件尺寸这类无关细节，除非该尺寸本身就是要验收的行为。

## 启动

Godot 捕获不了脚本报错，编辑器运行和真包也不一致。测试由一个 Python 脚本启动。它调用项目里的 `.engine.bat` / `.engine.sh`（见 [setup.md](setup.md)），不写死本机 Godot 路径。版本和安装目录在 `project.godot` 的 `[engine_host]`。测试入口 Autoload 也写在这个文件里。一次只跑一个：

```text
python .engine_test.py
python .engine_test.py --id-smoke
python .engine_test.py --id-monkey
```

`--id-` 后面是测试名。不写参数就是 `smoke`。`--id-smoke` 和默认是同一条。

顺序固定：

1. 把 debug 包导出到临时目录下的 GUID 子目录，避免并发写到同一路径。导出时引擎会自己导入资源。
2. 用该包跑对应的 GDScript，不在编辑器里跑。
3. 转发 Godot 的 stdout / stderr，供看日志。
4. 输出里一出现错误或警告就立刻停，不等测试自己退出，也不等超时。

`TESTS` 的值是 `res://tests/.../*.gd`。导出包不接受编辑器的场景路径。Autoload `tests/test_entry.gd` 读 `--test=`，脚本必须 `extends Node`，`load` 后 `new()`，挂到自己下面。不要 `set_script()`。

模板在 [project-template/.engine_test.py](project-template/.engine_test.py)，和 `.engine.bat` / `.engine.sh` 一起在安装时拷进仓库。它只通过这两个脚本启动引擎。默认测试是 [project-template/tests/smoke.gd](project-template/tests/smoke.gd)。其它测试加进 `TESTS`。
