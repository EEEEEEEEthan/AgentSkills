# 环境安装

如果项目已经有自己的启动器和测试流程,则本文档不适用.

需要询问用户:
引擎版本,也包括flavor

把本技能的 `project-template/` 拷到仓库根。
如有文件覆盖,仔细斟酌,有必要时询问用户. 重点是部署一键启动编辑器和一键测试,即保障`.engine.py`和`.engine_test.py`功能通畅.`.engine.py`无参数打开编辑器,有参数时转给引擎.

不需要额外下载引擎或导出模板。版本和安装目录写在 `project.godot` 的 `[engine_host]`。`.engine.py` 发现本机没有对应引擎时会自己下载到 `install_directory`。`.engine_test.py` 发现没有对应导出模板时会自己下载到 Godot 默认目录（Windows 为 `%APPDATA%\Godot\export_templates\<版本>\`）。
