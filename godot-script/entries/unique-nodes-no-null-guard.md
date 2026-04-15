# Unique 节点：不要为「必有」子节点写多余 null 检查

## 问题

对标记为 unique、场景中应始终存在的节点做 `if node:`，会掩盖配置错误，难调试。

## 错误示例

```gdscript
func _refresh_title():
    var label = %TitleLabel
    if label:  # ❌ unique 应始终存在
        label.text = title
```

## 正确做法

```gdscript
@onready var title_label: Label = %TitleLabel

func _refresh_title():
    title_label.text = title  # ✅ 缺失则立刻报错
```

## 例外

节点**确实**可能不存在时，用 `get_node_or_null()` 并显式处理 `null`。

## 为什么重要

问题在开发期暴露，而不是运行时静默不更新 UI。
