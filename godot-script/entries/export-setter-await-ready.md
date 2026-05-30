# 导出 setter 内 `await ready`：就绪后再访问子节点

## 适用

根脚本挂在 **场景实例根**（与 `.tscn` 中子节点同层或父层）上，setter 必须把导出值写到**子节点**（`%` 唯一名等），且接受 setter 在「未 ready」时挂起直到本节点 `ready`。

## 依据

本节点发出 `ready` 时，引擎已先完成子树中更深层节点的 `_ready()`，再执行本节点 `_ready()`，最后才标记本节点 `is_node_ready()` 并发出 `ready`。因此在 setter 里 `await ready` 返回后，同场景内已声明的子节点（如 `%DamageLabel`）已在树内且其 `_ready()` 已跑过，可安全访问。

## 写法

```gdscript
@export var text: String = "":
	set(value):
		text = value
		if not is_node_ready():
			await ready
		%SomeChild.text = value
```

已 ready 时分支跳过 `await`，直接同步子节点。

## 与 `is_node_ready()` + `_ready()` 刷新的取舍

- **`await ready`**：单一路径写在 setter，不必另写 `_refresh_*()` 再在 `_ready()` 里重复调用；注意 setter 会变成可 `await` 的协程，调用方若在「未 ready 赋值」路径上要理解异步语义。
- **`is_node_ready()` + `_ready()` 统一刷新**：同步友好、与「不在 setter 里挂起」的代码风格一致；需维护 `_refresh_*` 与 `_ready()` 双处调用。

## 常见误用

- 在 **非本节点** 的 `ready` 上错误地 `await`（例如子节点脚本里 `await get_parent().ready` 却在本帧提前访问兄弟子节点），顺序与上述保证不一致，仍可能踩坑。
- 访问的是 **运行时动态添加**、尚未 `add_child` 的节点——与本条「场景子树已存在」前提不符。
