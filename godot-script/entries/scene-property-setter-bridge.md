# 场景属性桥接：setter-only + await ready

挂在 `.tscn` 上的脚本若要把状态暴露给 C# 或其它调用方，并同步到子控件，优先用**只有 setter 的属性**；刷新写在 setter 内，用 `await ready` 保证子树就绪，**尽量不要在 `_ready` 里再刷一遍**（万不得已才在 `_ready` 补一次）。

## 范式

1. **getter 可省略**：只写 setter；`prop = v` 写入隐式后备，外部仍可读（见 [property-setter-self-assign.md](property-setter-self-assign.md)）。
2. **setter 顺序**：先 `prop = v` → `if not is_node_ready(): await ready` → 用 `%` 写子节点 / 发信号。
3. **子节点**：默认直接 `%UniqueName`；子控件还要等自身 `_ready()`（布局等）时，再 `if not node.is_node_ready(): await node.ready`。
4. **`_ready`**：只放与「属性→子节点」无关的事（如 `value_changed`、`gui_input` 连接）；属性初值靠 setter + `await ready` 单路径覆盖，避免 `_ready` 与 setter 各写一份。

## 示例（`OptionSliderRow.tscn`）

```gdscript
var value: float:
	set(v):
		value = v
		if not is_node_ready(): await ready
		%Slider.value = v

@export var label_text: String = "":
	set(value):
		label_text = value
		if not is_node_ready(): await ready
		%Label.text = value
```

桥接属性（`min` / `max` / `step` / `value`）与 `@export` 标题类属性共用同一写法；C# 用 `Set("value", x)`、`Connect("value_changed", …)`，不暴露内部 `Slider`。

### 多个导出属性

每个 setter 各自 `await ready`（已 ready 时几乎无成本），可共用 `_apply_*`。

```gdscript
@export var text: String = "":
	set(value):
		text = value
		if not is_node_ready(): await ready
		%Label.text = text

@export var icon_texture: Texture2D:
	set(value):
		icon_texture = value
		if not is_node_ready(): await ready
		%Icon.texture = icon_texture
```

## 常见错误

- 在 `_ready` 里再写 `%Label.text = label_text`（与 setter 重复，改一处易漏另一处）。
- setter 里**先**访问 `%` 子节点、**后** `await ready`（编辑器实例化阶段会失败）。
- 为桥接单独写 getter + `_backing`（除非 `RefCounted` 等，见 [refcounted-backing-properties.md](refcounted-backing-properties.md)）。

## 关联

- [property-setter-self-assign.md](property-setter-self-assign.md) — 同名赋值与省略 getter
- [onready-cache-percent.md](onready-cache-percent.md) — 热路径才缓存，桥接 setter 里用 `%` 即可
