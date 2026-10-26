# Godot 引擎最佳实践

资源管理、tscn 结构、场景边界与引擎行为。先读本文件；落到具体问题时再读对应条目。

能写成 `.tscn` 的结构、引用和信号连接就写进场景；运行时只做场景表达不了的行为。
[entries/prefer-static-tscn.md](entries/prefer-static-tscn.md)

目录按功能分，不建 `scripts/`、`tscns/`、`assets/`。某个 tscn 和只有它引用的资源放同一目录：根脚本是同目录同名薄 `.gd`，其余逻辑放子节点 builtin。第二处引用出现时拿到共同上层；上层太挤时再开该层的公共目录。继承场景例外。
[entries/group-by-feature.md](entries/group-by-feature.md)

每个 `.tscn` 不访问场景树外节点/其它 tscn；与父级等通讯用信号；Autoload 可直接访问。
[entries/tscn-signal-boundary.md](entries/tscn-signal-boundary.md)

unique name / `%` 只能在同一个 tscn 内互用。跨子 tscn 或外部 tscn 时编辑器能过、打包运行报错；外部只调子场景根上的功能 API，不要用属性把内部节点交出去。
[entries/unique-name-only-within-same-tscn.md](entries/unique-name-only-within-same-tscn.md)

场景根 `.gd` 不写仅为子节点信号中转的 `_on_*`；子节点 builtin 用 `owner` 调根上 API，场景外连 public 方法。
[entries/tscn-root-no-child-relay-handlers.md](entries/tscn-root-no-child-relay-handlers.md)

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
