# Godot 自动化测试最佳实践

每条测试都是 `tests` 目录下一层的 `extends Node` 脚本，文件名不以 `_` 开头。`_test_entry.gd` 是入口，不参与测试。不带参数时跑 `smoke`。CI 跑 `--all`。不要为测试建 `.tscn`。不要递归子目录。

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
python .engine_test.py --all
```

`--id-` 后面是测试名。不写参数就是 `smoke`。`--id-smoke` 和默认是同一条。`--all` 并发跑上述全部 gd。有一项失败就停掉其余项，并写出 `$ID测试失败, 详细报告见临时文件目录/$PROJECT_NAME/test/export_$GUID/tests/$ID/test_log.txt`。全部成功才结束。

顺序固定：

1. 打一份 debug 包到临时文件目录下的 `$PROJECT_NAME/test/export_$GUID/` 根目录，各项测试共用。`$PROJECT_NAME` 是仓库目录名。每项的运行目录是 `export_$GUID/tests/$ID/`，日志是 `export_$GUID/tests/$ID/test_log.txt`。`_test_entry.gd` 按运行目录把 `user://` 隔开。导出时引擎会自己导入资源。
2. 用该包跑对应的 GDScript，不在编辑器里跑。
3. 转发 Godot 的 stdout / stderr，供看日志。
4. 输出里一出现错误或警告就立刻停，不等测试自己退出，也不等超时。

`tests` 目录下一层、不以 `_` 开头的 gd 都会被 `--all` 纳入。导出包不接受编辑器的场景路径。Autoload `tests/_test_entry.gd` 读 `--test=`，脚本必须 `extends Node`，`load` 后 `new()`，挂到自己下面。不要 `set_script()`。

模板在 [project-template/.engine_test.py](project-template/.engine_test.py)，和 `.engine.bat` / `.engine.sh` 一起在安装时拷进仓库。它只通过这两个脚本启动引擎。默认测试是 [project-template/tests/smoke.gd](project-template/tests/smoke.gd)。其它测试放在 `tests` 目录下一层。
