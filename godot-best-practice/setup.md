# 环境安装

如果项目已经有自己的启动器和测试流程,则本文档不适用.

需要询问用户两件事:
- 引擎版本,也包括 flavor
- 是否用 C#/.NET(dotnet)

把本技能的 `project-template/` 拷到仓库根。
如有文件覆盖,仔细斟酌,有必要时询问用户. 重点是部署一键启动编辑器和一键测试,即保障`.engine.py`和`.engine_test.py`功能通畅.`.engine.py`无参数打开编辑器,有参数时转给引擎.

不需要额外下载引擎或导出模板。版本、flavor、是否用 .NET 和安装目录都写在 `project.godot` 的 `[engine_host]`；`version` / `flavor` / `install_directory` / `dotnet` 缺失时用默认值 `4.8` / `beta2` / `~/godots` / `"false"`。`.engine.py` 发现本机没有对应引擎时会自己下载到 `install_directory`。`.engine_test.py` 发现没有对应导出模板时会自己下载到 Godot 默认目录（Windows 为 `%APPDATA%\Godot\export_templates\<版本>\`）。

## C#/.NET 是安装时勾选项

用户说用 C#/.NET 时, 把 `[engine_host] dotnet` 改成 `"true"`（模板默认是 `"false"`，字段一直留在文件里, 随时可切）。勾选后的差异：

- 引擎改下 mono 版（`mono_win64.zip` / `mono_linux.x86_64.zip` / `mono_macos.<架构>.zip`），装到 `<install_directory>/<version>-<flavor>-dotnet/`，与标准引擎并存，互不覆盖。
- 导出模板改下 `mono_export_templates.tpz`。
- `.engine_test.py` 在导出前先跑一次 `--build-solutions`：全新检出既没有 C# 程序集也没有全局类缓存，不构建的话 GDScript 会解析不到 C# 的 `[GlobalClass]`。

dotnet 只影响引擎、导出与构建。测试脚本仍然是 `tests/` 下的 GDScript（`smoke` 等），不依赖 C#。
