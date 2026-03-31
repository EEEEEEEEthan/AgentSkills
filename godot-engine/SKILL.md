---
name: godot-engine
description: Godot 引擎使用与行为规范
---

# Godot 引擎使用

## InstancePlaceholder：create_instance 与 instantiate 的时机差异

**问题**：`InstancePlaceholder.create_instance()` 会立即将实例加入场景树（替换 placeholder），从而触发 `_ready()`。若需在 `_ready` 前完成依赖注入（如 `inspector.bot = self`），此时注入尚未执行，`_ready` 内访问会得到 null。

**正确做法**：用 `load(placeholder.get_instance_path()).instantiate()` 替代 `create_instance()`。`instantiate()` 创建节点但不加入树，可先完成注入再 `add_child()`，`_ready` 执行时依赖已就绪。

**路径维护**：保留 placeholder 在场景中，用 `get_instance_path()` 动态获取路径。移动场景文件时，只需在编辑器中更新 placeholder 引用，优于硬编码 `preload("res://path.tscn")`。

```gdscript
# ✅ 正确：instantiate 不加入树，先注入再 add_child
var placeholder: InstancePlaceholder = $BotInspector
var inspector: Window = load(placeholder.get_instance_path()).instantiate()
inspector.bot = self
get_tree().root.add_child(inspector)
```

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

需要在本帧内拿到正确的布局或尺寸时：

1. **先触发布局**：对相关 Container 调用 `FlushLayout()`（C# 扩展）或 `queue_sort()` / 依赖引擎的排序机制，使排序与 `UpdateMinimumSize()` 在本帧内完成。
2. **再读尺寸或执行逻辑**：在同一帧内调用 `GetCombinedMinimumSize()`、读取 `Size`/`Position` 或设置窗口位置等。

**不要**为“等布局算好”而延迟到下一帧：禁用 `CallDeferred(nameof(UpdateLayout))`、`await get_tree().process_frame` 等，再在下一帧读尺寸或执行逻辑。

**正确示例**（C#）：在 `UpdateWindowLayout()` 里先 `PanelContainer.FlushLayout()`，再 `PanelContainer.GetCombinedMinimumSize()`。

## C# API 成本：少用引擎 API

Godot 的 C# 绑定与引擎交互（P/Invoke）成本较高。应尽量减少对引擎属性的读写。

**Engine.IsEditorHint()** 是昂贵调用，每次都会跨越托管/原生边界。若多处使用，应封装并缓存（用 `??=` 或类似方式首次求值后复用）。

**适用场景**：每帧更新坐标、旋转等属性时，可做本地缓存，仅在值变化时写回引擎。

**做法**：用属性封装，内部维护 `Vector3?` 等缓存字段；setter 内先 `if(cache == value) return`，再同时更新缓存和 `Node.Position`/`Camera.Rotation` 等。
