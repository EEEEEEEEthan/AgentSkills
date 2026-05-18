# 场景属性桥接：setter-only + await ready

挂在 `.tscn` 上的脚本若要把状态暴露给 C# 或其它调用方，并同步到子控件，优先用**只有 setter 的属性**；刷新逻辑写在 setter 内，**不要在 `_ready` 里重复一份**。

## 范式

1. **getter 可省略**：只写 setter；`prop = v` 写入隐式后备，外部仍可读（见 [property-setter-self-assign.md](property-setter-self-assign.md)）。
2. **setter 顺序**：先 `prop = v` → `if not is_node_ready(): await ready` → 写子节点 / 发信号。
3. **`_ready` 只放与「属性→子节点」无关的事**（如连接 `value_changed`、`gui_input`）。

## 示例（`OptionSliderRow.tscn`）

```gdscript
var value: float:
	set(v):
		value = v
		if not is_node_ready(): await ready
		_slider.value = v

@export var label_text: String = "":
	set(value):
		label_text = value
		if not is_node_ready(): await ready
		%Label.text = value
```

桥接属性（`min` / `max` / `step` / `value`）与 `@export` 标题类属性共用同一写法；C# 用 `Set("value", x)`、`Connect("value_changed", …)`，不暴露内部 `Slider`。

## 常见错误

- 在 `_ready` 里再写一遍 `%Label.text = label_text`（与 setter 重复，初始值改一处易漏另一处）。
- 为可读性单独写 getter + `_backing`，而实际只需要 setter 同步子节点（除非 `RefCounted` 等需显式后备，见 [refcounted-backing-properties.md](refcounted-backing-properties.md)）。
- setter 里先访问子节点、后 `await ready`（编辑器实例化阶段会失败）。

## 关联

- [export-ready-scene-nodes.md](export-ready-scene-nodes.md) — `await ready` 时机与子节点 `ready`
- [property-setter-self-assign.md](property-setter-self-assign.md) — 同名赋值与省略 getter
