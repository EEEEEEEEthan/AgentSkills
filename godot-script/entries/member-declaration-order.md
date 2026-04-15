# 成员声明顺序：字段 → 属性 → 方法

## 原则

先字段，再属性（含 getter/setter），最后方法。

## 示例

```gdscript
var _move_task: BotTaskMove
var _cancel_flag: RefCounted

var is_cancelled: bool:
	get:
		return _move_task.aborted

func _ready() -> void:
	pass
```

## 为什么重要

属性常依赖字段；统一顺序便于扫读与 code review。
