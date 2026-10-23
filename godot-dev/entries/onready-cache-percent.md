# 访问 unique 节点：默认 `%`，热路径才 `@onready` 缓存

## 默认

子节点用场景 unique 名时，**直接 `%UniqueName`** 即可，不必为「少一次查找」默认加 `@onready`。

```gdscript
@export var label_text: String = "":
	set(value):
		label_text = value
		if not is_node_ready(): await ready
		%Label.text = value
```

## 何时 `@onready` 缓存

仅在**热路径**（每帧 `_process` / `_physics_process`、高频信号回调、循环内多次访问同一节点）时，用 `@onready` 在进树时解析一次，避免反复 `%` 查找：

```gdscript
@onready var title_label: Label = %TitleLabel

func _physics_process(_delta: float) -> void:
	title_label.text = _format_title()  # 每帧调用，值得缓存
```

setter、偶发刷新、属性桥接等**非热路径**继续用 `%`。

## 常见错误

- 为所有 `%` 一律加 `@onready`（增加字段、与 `@export` 顺序纠缠，收益通常很小）。
- 热路径里仍每次 `%Label` 查找（应缓存）。

## 为什么重要

- `%` 写法短、与 unique 名一致，配置错会立刻报错（见 [unique-nodes-no-null-guard.md](unique-nodes-no-null-guard.md)）。
- `@onready` 保留给确有性能或每帧访问需求的代码。
