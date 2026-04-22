---
name: godot-script
description: 编写gdscript必读
---

# Godot 脚本最佳实践

新编写的代码请严格按照编码风格进行编码
[entries/style-guide.md](entries/style-guide.md)

挂在场景（tscn）上的脚本：导出属性若在 setter 里要访问子节点，须在 `is_node_ready()` 之后，并在 `_ready()` 统一同步到场景
[entries/export-ready-scene-nodes.md](entries/export-ready-scene-nodes.md)

用 `@onready` 缓存 `%` 节点，避免每次刷新都重新查找
[entries/onready-cache-percent.md](entries/onready-cache-percent.md)

子节点要访问所属场景根时用 `owner`，不要用 `get_parent()` 硬链
[entries/owner-vs-get-parent.md](entries/owner-vs-get-parent.md)

对场景中应存在的 unique 节点不要写多余 null 检查，让错误尽早暴露
[entries/unique-nodes-no-null-guard.md](entries/unique-nodes-no-null-guard.md)

成员顺序：字段 → 属性（含 getter/setter）→ 方法
[entries/member-declaration-order.md](entries/member-declaration-order.md)

属性 setter 内对同名赋值由引擎写入隐式后备存储；无自定义 getter 时不必再声明 `_x` 后备字段，只写 setter 即可
[entries/property-setter-self-assign.md](entries/property-setter-self-assign.md)

`RefCounted` 等数据类要在 setter 发信号或副作用时，用显式 `_backing` + getter/setter
[entries/refcounted-backing-properties.md](entries/refcounted-backing-properties.md)

# 维护此文档

在正文列表中增加一行摘要 + `entries/` 链接，在 `entries/` 下新增对应详述；条目保持短小可检索，不扩成替代官方文档的教程。
