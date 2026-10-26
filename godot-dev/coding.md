# Godot 编码最佳实践

GDScript 与 C#。先读本文件里对应语言的小节；落到具体问题时再读条目。

## GDScript

新编写的代码请严格按照编码风格进行编码
[entries/style-guide.md](entries/style-guide.md)

场景属性桥接（setter-only：先赋值、`await ready` 再写子节点；优先 `%`；getter 可省略；尽量不在 `_ready` 刷 UI）
[entries/scene-property-setter-bridge.md](entries/scene-property-setter-bridge.md)

本节点 `ready` 发出时，同场景已声明子节点的 `_ready()` 已经跑完；setter 写法仍以场景属性桥接为准。
[entries/export-setter-await-ready.md](entries/export-setter-await-ready.md)

访问**本 tscn** 的 unique 子节点默认用 `%`；仅热路径（如每帧）才 `@onready` 缓存。不能跨进子 tscn 或外部 tscn。
[entries/onready-cache-percent.md](entries/onready-cache-percent.md)
[entries/unique-name-only-within-same-tscn.md](entries/unique-name-only-within-same-tscn.md)

子节点要访问所属场景根时用 `owner`，不要用 `get_parent()` 硬链
[entries/owner-vs-get-parent.md](entries/owner-vs-get-parent.md)

对场景中应存在的 unique 节点不要写多余 null 检查，让错误尽早暴露
[entries/unique-nodes-no-null-guard.md](entries/unique-nodes-no-null-guard.md)

属性 setter 内对同名赋值由引擎写入隐式后备存储；无自定义 getter 时不必再声明 `_x` 后备字段，只写 setter 即可
[entries/property-setter-self-assign.md](entries/property-setter-self-assign.md)

`Resource` / `RefCounted` 数据类同样用 setter 自赋值 + 隐式后备，不必显式 `_backing`；仅构造期需绕过 setter 时例外
[entries/refcounted-backing-properties.md](entries/refcounted-backing-properties.md)

只等信号一次时直接 `await`，不要为这一次另写 `_on_*`
[entries/await-signal-once.md](entries/await-signal-once.md)

读的是稳定状态用属性；每次调用都新建对象时用 `new_` / `create_`，不要用 `get_`
[entries/property-vs-method-naming.md](entries/property-vs-method-naming.md)

懒加载资源用与语义同名的 `var` + getter，每一项只判断自己的成员
[entries/lazy-resource-same-name-getter.md](entries/lazy-resource-same-name-getter.md)

编写或审查 GDScript 时对照清单
[entries/review-checklist.md](entries/review-checklist.md)

## C#

在 C# 中把引擎 API 当成高成本边界，优先缓存、合并写回并减少重复跨边界调用。
[entries/csharp-api-cost.md](entries/csharp-api-cost.md)

占位符用 `GetNode<InstancePlaceholder>`，不要另写死 `res://` 路径，也不要 `Duplicate()`。进树前要注入依赖时走 `GetInstancePath()`，否则 `CreateInstance()`。本 tscn 内部节点用 unique name + `field ??=`，不对仅由场景结构决定的引用做 `[Export]`；unique name 不能跨 tscn。
[entries/csharp-scene-access.md](entries/csharp-scene-access.md)
