# 数据模型：显式后备字段 + getter/setter

## 场景

`RefCounted` / 纯数据类（非 Node）中，写入时需要发信号、校验或统一副作用；与节点上 `@export` 依赖引擎隐式存储的写法区分开。

setter 里写 `value = v` 本身在 GDScript 中**合法且可靠**（见 [property-setter-self-assign.md](property-setter-self-assign.md)）；此处显式 `_value` 多为**构造期少 `emit`**、可读性或规范，而非否定自赋值语法。

## 正确做法（与仓库 `game/character/property.gd` 一致）

```gdscript
var _value: float

var value: float:
	get:
		return _value
	set(v):
		_value = v
		changed.emit()
```

## 要点

- 实际数据放在 `_value`、`_max_value` 等后备字段；对外 `value` 负责入口与副作用。
- `_init` 里若不想构造阶段反复 `emit`，可直接写 `_value = v`。

## 与 Node `@export` 的区别

节点脚本里常见 `set(x): title = x` 配合隐式存储；**数据类**要明确「存哪、何时发信号」时，优先显式 `_backing` + getter/setter。

## 完整示例：可观察数值

```gdscript
class_name ExampleStat

signal changed

var _value: float
var _max_value: float

var value: float:
	get:
		return _value
	set(v):
		_value = v
		changed.emit()

var max_value: float:
	get:
		return _max_value
	set(v):
		_max_value = v
		changed.emit()

func _init(v: float, max_v: float) -> void:
	_value = v
	_max_value = max_v
```
