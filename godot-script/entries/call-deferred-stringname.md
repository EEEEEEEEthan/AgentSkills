# `call_deferred` 方法名用 `StringName`

## 问题

`call_deferred("method_name", args)` 用普通字符串，易拼写错误且无类型提示。

## 正确做法

```gdscript
object.call_deferred(&"move_by", direction, callback)
```

## 常见错误

```gdscript
object.call_deferred("move_by", direction, callback)  # ❌ 应使用 &"move_by"
```

## 为什么重要

Godot 4 中方法名推荐 `StringName`；`call_deferred` 只能传方法名字符串，用 `&"..."` 更一致。
