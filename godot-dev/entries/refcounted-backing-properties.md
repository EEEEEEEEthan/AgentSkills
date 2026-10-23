# Resource / RefCounted：同样不必显式后备字段

## 结论

`Resource`、`RefCounted` 等数据类与 Node 一样：setter 里对同名属性赋值写入**隐式后备存储**，**不会**递归进 setter。发 `emit_changed()` / 自定义信号时，**默认只写 setter、省略 getter，不要**再声明 `_x`。

见 [property-setter-self-assign.md](property-setter-self-assign.md)。

## 推荐写法

```gdscript
@export var team_alm: TeamData = TeamData.new():
	set(value):
		if team_alm == value:
			return
		team_alm = value
		emit_changed()
```

```gdscript
var value: float = 0.0:
	set(v):
		if value == v:
			return
		value = v
		changed.emit()
```

## 何时才用显式 `_backing`

仅当**必须绕过 setter** 写存储时（例如 `_init` 里不想触发 `emit`），才用 `_value` + getter/setter。这是例外，不是数据类默认规范。

```gdscript
var _value: float

var value: float:
	get:
		return _value
	set(v):
		_value = v
		changed.emit()

func _init(v: float) -> void:
	_value = v  # 绕过 setter，构造期不 emit
```
