# 用 `InstancePlaceholder` 做可重复生成的子场景

## 问题

用 `@export var bullet_scene: PackedScene` 在检视器里再拖一份子弹场景，与场景树里「占位符已指向 bullet」重复，改路径容易漏一处。

## 推荐做法

在 `gun.tscn` 等场景里勾选 **Load as Placeholder**，保留 `InstancePlaceholder`；脚本里 `@onready var _bullet_placeholder: InstancePlaceholder = %BulletPlaceHolder`，生成时：

```gdscript
var spawned := _bullet_placeholder.create_instance() as Bullet  # 默认 replace=false
remove_child(spawned)
game.add_child(spawned)
# 再写 global_position、velocity 等
```

`create_instance()` 在 Godot 4 默认 **`replace=false`**：新节点与占位符**同级**，占位符仍在，可连发、循环 `bullets_per_shot` 多次调用。

## 何时不用 `create_instance`

占位符上存的属性会在 `create_instance` 时按引擎规则应用；若必须在**进树前**注入且目标 `_ready()` 会立刻读这些依赖，改用 `load(placeholder.get_instance_path()).instantiate()`，配好后再 `add_child`（见引擎侧 `instance-placeholder` 说明）。

## 常见错误

- 误传 `replace=true`：会替换掉占位符，后续调用失效。
- 需要子弹挂在 `Game` 等根下时，记得先从枪节点 `remove_child` 再 `add_child` 到目标父节点。
