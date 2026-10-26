# unique name 只在同一个 tscn 内有效

## 坑

跨 tscn 访问 unique name：编辑器里正常，打包运行报错。

`unique_name_in_owner` / `%` / `GetNode("%...")` 只能在**同一个** `.tscn` 里互相用。

- 有子 tscn 时，不能直接访问子 tscn 的 unique 节点。
- 也不能访问外部 tscn 的 unique 节点。

## 正确做法

子 tscn 提供特定功能 API，让外部访问。外部只调用子场景**根**上的方法（或连接根上的信号）。

尽量不要直接提供属性去访问某个节点。tscn 应该是个黑盒：暴露的功能越少越好，外部越不需要理解黑盒的结构越好。

```gdscript
# ❌ 父场景钻进子场景的 unique 节点（编辑器能过，打包运行报错）
%HealthBar.fill_amount = ratio

# ✅ 子场景根提供功能；% 留在 health_bar.tscn 自己的脚本里
%HealthBar.set_health_ratio(ratio)
```

```gdscript
# health_bar.gd（子场景根）
func set_health_ratio(ratio: float) -> void:
	%Fill.scale.x = ratio
```

本 tscn 里声明的节点（含本场景内的 builtin）继续用 `%`，见 [onready-cache-percent.md](onready-cache-percent.md)。
