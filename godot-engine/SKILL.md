---
name: godot-engine
description: Godot 引擎使用与行为规范。用于处理引擎对象生命周期、布局刷新、尺寸读取、InstancePlaceholder、CallDeferred、process_frame、Engine.IsEditorHint 与 C# 调用成本相关问题时。
---

# Godot 引擎使用

## 使用方式

先读本文件，只拿总规则。

当任务落到具体问题时，再按需读取对应文档：

- `InstancePlaceholder`、依赖注入、`_ready()` 时机：见 [instance-placeholder.md](instance-placeholder.md)
- 容器布局、尺寸读取、同帧刷新：见 [layout-refresh.md](layout-refresh.md)
- `Engine.IsEditorHint()`、引擎属性访问、C# 调用成本：见 [csharp-api-cost.md](csharp-api-cost.md)

## 总规则

1. 涉及时序时，先确认节点是否已经进树，再决定是否能访问依赖或尺寸。
2. 需要“本帧得到结果”时，优先显式触发布局或更新，不要默认拖到下一帧。
3. 在 C# 中把引擎 API 当成高成本边界，避免重复读写。
4. 默认优先稳定、可维护的路径与生命周期方案，避免依赖脆弱时机。

## 防误改的tscn引用：子节点 Metadata（如 Config）

**问题**：关键 `PackedScene` / 资源引用若只放在根节点 `@export`、或易被合并与手滑覆盖的位置，场景协作或反复编辑时可能被无意改掉。

**做法**：为「不应被随便改掉」的引用建专用子节点（常见命名 **`Config`**），把引用写在**该子节点的 Metadata** 里（检视器 → 选中 `Config` → Metadata），由脚本 `get_node("%Config").get_meta("键", 默认值)` 或 `has_meta` 读取。

**要点**：

- 与节点绑定：Metadata 跟 `Config` 节点走，结构清晰，也便于在版本 diff 里单独辨认。
- 可选：给 `Config` 设 `process_mode = PROCESS_MODE_DISABLED`，不参与运行时代码路径以外的逻辑。
- 若需代码侧兜底，可在 `_ready` 里检测 `has_meta`，缺失时 `push_warning` 或回退到 `preload`。

```gdscript
# 示例：子弹场景引用存在 Config 子节点上
const META_BULLET_SCENE := "bullet_scene"

func _ready() -> void:
	var config: Node = get_node("Config")
	var bullet: PackedScene = config.get_meta(META_BULLET_SCENE) as PackedScene
```

**不适用**：需要频繁在检视器里拖拽替换、且不怕误改的普通 `@export`，仍可直接 export。

## 场景内信号：优先在检视器连接

**约定**：同一 `.tscn` 里、发射端与接收端都已存在的信号（如子节点 `Timer.timeout` → 根脚本方法），应在**检视器「节点」标签页的信号面板**里连接，并写入场景文件 `[connection ...]`，而不是在脚本的 `_ready()` 里 `signal.connect(Callable(...))`。

**原因**：连接关系在场景里一眼可见、合并冲突时好 diff、改方法名时编辑器可提示断连；代码里隐式连接不利于协作与审查。

**例外**：运行时动态创建节点、或连接目标依赖代码分支时，仍用代码连接。

## 布局刷新：同一帧内触发布局再读尺寸

细则与做法见 [layout-refresh.md](layout-refresh.md)，与总规则第 2 条一致。

## 快速分流

### 场景一：placeholder 替身节点要先注入依赖

不要急着 `create_instance()`，先看 [instance-placeholder.md](instance-placeholder.md)。

### 场景二：这帧就要读到正确尺寸或位置

不要先 `CallDeferred` 或 `await process_frame`，先看 [layout-refresh.md](layout-refresh.md)。

### 场景三：C# 逻辑里频繁访问引擎对象

先检查是否能缓存、合并写回或减少跨边界调用，具体见 [csharp-api-cost.md](csharp-api-cost.md)。
