# 已知方法直接调用，场景根用 class_name

## 坑

`node.call("reachable_distance")` 把方法名变成字符串。改名、改参数时编译器不报错，返回值也丢掉类型，调用处还要再 `float()` 或 `as`。

节点只标成 `Node` / `Node2D` 时，脚本上的方法看不见，就只好 `call`。

## 正确做法

子场景根要被别的脚本调用时，在它的 `.gd` 上写 `class_name`。调用方把节点收成这个类型，然后直接调用。

只用一次、又不需要被外场景当类型用的脚本，仍按嵌入脚本那条留在 `.tscn` 里。需要 `class_name` 时才把脚本拆成同目录的 `.gd`。

```gdscript
# hand.gd
class_name Hand
extends Node2D

var reachable_distance: float:
	get:
		return _reach_distance(MAX_EXTENSION)
```

```gdscript
# ❌
var hand: Node2D = get_node("LeftHand")
var reach := float(hand.call("reachable_distance"))

# ✅
var reach := _character.left_hand.reachable_distance
```
