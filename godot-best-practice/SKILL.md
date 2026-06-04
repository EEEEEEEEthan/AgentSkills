---
name: godot-best-practice
description: Godot 场景架构最佳实践（根脚本与 builtin 分工、场景信号边界、根脚本不写子节点 _on 中转）。编写或审查 .tscn/.gd、重构场景通讯、拆分脚本时使用。
---

# Godot 场景架构

先读本文件索引；落到具体问题时再读对应条目。

除**继承场景**外：根脚本为同文件夹同名 `.gd`（尽量薄，作对外边界）；具体功能在 tscn 内子节点 builtin 实现（可访问场景内含私有成员），除非有复用可能。
[tscn-root-script-same-name-gd.md](tscn-root-script-same-name-gd.md)

每个 `.tscn` 不访问场景树外节点/其它 tscn；与父级等通讯用信号；Autoload 可直接访问。
[tscn-signal-boundary.md](tscn-signal-boundary.md)

场景根 `.gd` 不写仅为子节点信号中转的 `_on_*`；子节点 builtin 用 `owner` 调根上 API，场景外连 public 方法。
[tscn-root-no-child-relay-handlers.md](tscn-root-no-child-relay-handlers.md)

# 维护此文档

在索引部分增加一句话描述和文档链接，并在同目录新增对应的详细说明文档。
