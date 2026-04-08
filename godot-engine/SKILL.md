---
name: godot-engine
description: Godot 引擎使用与行为规范。用于处理 Godot 节点生命周期、布局刷新、InstancePlaceholder、场景信号连接、CanvasItem 共享材质与 C# 引擎交互成本问题。
---

# Godot 引擎使用

先读本文件，只拿索引；落到具体问题时，再按需读对应文档。

节点是否已经进树，会直接决定能否安全访问依赖、尺寸和生命周期相关状态。
[lifecycle-tree-timing.md](lifecycle-tree-timing.md)

已勾选加载为占位符的子项，运行时是 `InstancePlaceholder`，需要先注入依赖时不要直接 `create_instance()`。
[instance-placeholder.md](instance-placeholder.md)

需要“本帧得到结果”时，优先显式触发布局或更新，不要默认拖到下一帧。
[layout-refresh.md](layout-refresh.md)

在 C# 中把引擎 API 当成高成本边界，优先缓存、合并写回并减少重复跨边界调用。
[csharp-api-cost.md](csharp-api-cost.md)

不应被随手改掉的关键场景资源引用，优先放到子节点 Metadata，而不是根节点普通 `@export`。
[config-metadata.md](config-metadata.md)

同一 `.tscn` 内两端都已存在的静态信号，优先在检视器里连接并写入场景文件。
[scene-signals-inspector.md](scene-signals-inspector.md)

CanvasItem shader 想共享材质时，不要把 `sampler2D` 当作 `instance uniform`；改用节点自带纹理通道或别的共享承载方式。
[canvas-item-shared-material-textures.md](canvas-item-shared-material-textures.md)

# 维护此文档

在索引部分增加一句话描述和文档链接，并在同目录新增对应的详细说明文档。
