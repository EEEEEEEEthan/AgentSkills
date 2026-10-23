---
name: godot-dev
description: Godot 开发规范（场景架构、引擎行为、编码规范等）
---

# Godot 开发

先读本文件索引；落到具体问题时再读对应条目。

## 场景架构

除**继承场景**外：根脚本为同文件夹同名 `.gd`（尽量薄，作对外边界）；具体功能在 tscn 内子节点 builtin 实现（可访问场景内含私有成员），除非有复用可能。
[entries/tscn-root-script-same-name-gd.md](entries/tscn-root-script-same-name-gd.md)

每个 `.tscn` 不访问场景树外节点/其它 tscn；与父级等通讯用信号；Autoload 可直接访问。
[entries/tscn-signal-boundary.md](entries/tscn-signal-boundary.md)

unique name / `%` 只能在同一个 tscn 内互用。跨子 tscn 或外部 tscn 时编辑器能过、打包运行报错；外部只调子场景根上的功能 API，不要用属性把内部节点交出去。
[entries/unique-name-only-within-same-tscn.md](entries/unique-name-only-within-same-tscn.md)

场景根 `.gd` 不写仅为子节点信号中转的 `_on_*`；子节点 builtin 用 `owner` 调根上 API，场景外连 public 方法。
[entries/tscn-root-no-child-relay-handlers.md](entries/tscn-root-no-child-relay-handlers.md)

## 引擎

节点是否已经进树，会直接决定能否安全访问依赖、尺寸和生命周期相关状态。
[entries/lifecycle-tree-timing.md](entries/lifecycle-tree-timing.md)

已勾选加载为占位符的子项，运行时是 `InstancePlaceholder`。要在 `_ready` 前注入依赖时不要直接 `create_instance()` / `CreateInstance()`，用 `get_instance_path()` 加载后再 `add_child`。不需要提前注入、且要重复生成时，用 `create_instance()`（默认 `replace=false`）。
[entries/instance-placeholder.md](entries/instance-placeholder.md)
[entries/instance-placeholder-spawn.md](entries/instance-placeholder-spawn.md)

需要“本帧得到结果”时，优先显式触发布局或更新，不要默认拖到下一帧。
[entries/layout-refresh.md](entries/layout-refresh.md)

关键状态对齐不要长期绑在 `_process` 里“下一帧再改”；易错一帧并造成闪烁，应在数据变更处同步处理。
[entries/frame-state-vs-process.md](entries/frame-state-vs-process.md)

不应被随手改掉的关键场景资源引用，优先放到子节点 Metadata，而不是根节点普通 `@export`。
[entries/config-metadata.md](entries/config-metadata.md)

只被引用一次的资源必须 builtin（嵌入 `.tscn`）；复用两次以上才拆独立 `.gd`。嵌入脚本避免参数名遮蔽引擎成员；`extends` 必须与挂载节点类型一致。
[entries/embedded-scene-script.md](entries/embedded-scene-script.md)

同一 `.tscn` 内两端都已存在的静态信号，优先在检视器里连接并写入场景文件。
[entries/scene-signals-inspector.md](entries/scene-signals-inspector.md)

CanvasItem shader 想共享材质时，不要把 `sampler2D` 当作 `instance uniform`；改用节点自带纹理通道或别的共享承载方式。
[entries/canvas-item-shared-material-textures.md](entries/canvas-item-shared-material-textures.md)

独立子窗口关闭垂直同步时，交换链可能短暂呈现旧帧，表现为相机/画面被拉回；与 Camera2D clear 无关，优先检查 VSync。
[entries/vsync-subwindow-render-snapback.md](entries/vsync-subwindow-render-snapback.md)

`set_script()` 在运行时替换脚本会破坏 `@onready`、残留状态、炸裂类型系统；脚本归属在 .tscn 里声明，运行时只读不写。
[entries/avoid-set-script.md](entries/avoid-set-script.md)

`preload()` 在解析期隐式加载、制造循环依赖、阻塞延迟加载；资源引用走 `@export` 写进 .tscn，运行时按需 `load()`。
[entries/avoid-preload.md](entries/avoid-preload.md)

默认不用 `call_deferred()`。先修树结构再用信号；defer 是最后手段。确属例外时，方法名用 `&"method_name"`，并在旁边写明原因。
[entries/avoid-call-deferred.md](entries/avoid-call-deferred.md)
[entries/call-deferred-stringname.md](entries/call-deferred-stringname.md)

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

# 维护此文档

在对应小节增加一句话摘要和 `entries/` 链接，并在 `entries/` 下新增详述。条目保持短小可检索，不扩成替代官方文档的教程。
