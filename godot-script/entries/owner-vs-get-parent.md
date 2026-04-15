# 访问场景根：用 `owner`，不用 `get_parent()` 链

## 问题

子节点需要场景根（如 `BotMain`）时，用 `get_parent()` 会随层级改动而指错对象。

## 错误示例

```gdscript
# State 是 Bot 的子节点，需要访问 BotMain
var bot_main = get_parent()  # ❌ 移到 StateMachine 下就失效
```

## 正确做法

```gdscript
var bot_main = owner as Node2D  # ✅ owner 指向所属场景根
```

## 何时用

子节点或子组件需要访问**所属场景**的根节点时。

## 为什么重要

重构节点树时不必改一串 `get_parent().get_parent()`。
