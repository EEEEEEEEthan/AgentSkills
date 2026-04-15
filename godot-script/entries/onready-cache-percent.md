# 用 `@onready` 缓存节点，避免每次 `%` 查找

## 问题

在函数里每次用 `%UniqueName` 查找节点，性能差且意图不清。

## 错误示例

```gdscript
func _refresh_title():
    var label = %TitleLabel  # ❌ 每次调用都查找
    label.text = title
```

## 正确做法

```gdscript
@onready var title_label: Label = %TitleLabel  # ✅ 在 _ready 时解析一次

func _refresh_title():
    title_label.text = title
```

## 常见错误

在刷新函数里反复 `%Label` 而非缓存引用。

## 为什么重要

- `@onready` 在 `_ready()` 前解析，性能更好。
- 类型提示完整，补全与重构更稳。
