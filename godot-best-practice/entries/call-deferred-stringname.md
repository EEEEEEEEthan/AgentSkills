# `call_deferred` 方法名用 `StringName`

默认不要调用 `call_deferred()`，见 [avoid-call-deferred.md](avoid-call-deferred.md)。只有该文列出的极少数例外成立、并且调用旁写了原因时，才用下面的写法。

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
