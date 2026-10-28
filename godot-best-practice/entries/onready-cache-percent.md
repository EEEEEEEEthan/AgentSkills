# 访问 unique 节点：直接用 `%`，有性能问题才 `@onready`

## 默认

子节点用场景 unique 名时，**直接 `%UniqueName`**。尽可能不用 `@onready`。`%` 只解析**本 tscn** 里的 unique 节点，不能跨进子 tscn 或外部 tscn，见 [unique-name-only-within-same-tscn.md](unique-name-only-within-same-tscn.md)。

```gdscript
@export var label_text: String = "":
	set(value):
		label_text = value
		if not is_node_ready(): await ready
		%Label.text = value
```

`_process` 里读 `%UpperArm`、`%Forearm`、`%Hand`、`%Fingertip`、`%Grip` 也直接用 `%`。

## 何时才 `@onready` 缓存

先用 `%`。量到这里的查找成了性能问题，再改成 `@onready`，进树时解析一次：

```gdscript
@onready var title_label: Label = %TitleLabel

func _physics_process(_delta: float) -> void:
	title_label.text = _format_title()
```

## 常见错误

- 为了少写一次查找，就给 `%` 加上 `@onready`。
- 还没量到性能问题，就按「热路径」把节点缓存起来。

## 为什么重要

- `%` 写法短、与 unique 名一致，配错会立刻报错（见 [unique-nodes-no-null-guard.md](unique-nodes-no-null-guard.md)）。
- 提前缓存增加字段，收益通常没有。
