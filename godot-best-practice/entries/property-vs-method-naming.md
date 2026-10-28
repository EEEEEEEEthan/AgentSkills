# 返回值风格：属性 vs `get_xxx` 方法

## 原则

- **读的是稳定状态 / 缓存结果**：优先用属性 getter，例如 `var is_cancelled: bool: get: return _move_task.aborted`。
- **无参、只是把已有节点或算好的值交出去**：写成属性，不要写成无参方法。`reachable_distance`、`grip_global_position`、`grip_anchor` 都属于这一类。
- **每次调用要新建对象或产生新实例**：不要叫 `get_xxx`，改用 `new_xxx`、`create_xxx` 等，避免被当成缓存引用。

```gdscript
# ❌ 无参 getter 方法
func grip_global_position() -> Vector2:
	return _grip.global_position

# ✅
var grip_global_position: Vector2:
	get:
		return _grip.global_position
```

## 为什么重要

`get_xxx` 容易被理解成「取已有引用」；命名与语义一致可减少误用。
