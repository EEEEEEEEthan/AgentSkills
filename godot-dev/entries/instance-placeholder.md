# InstancePlaceholder

## 问题

`InstancePlaceholder.create_instance()` 会立即把实例加入场景树并替换 placeholder。

这意味着：

- 节点会立刻进入树
- `_ready()` 可能马上执行
- 如果你还没做依赖注入，`_ready()` 内访问到的成员可能还是空

典型问题：

```gdscript
var inspector = placeholder.create_instance()
inspector.bot = self
```

这里 `inspector.bot = self` 发生得太晚，`_ready()` 已经可能先跑了。

## 默认做法

当你需要在 `_ready()` 前完成注入时，用：

1. `placeholder.get_instance_path()` 取路径
2. `load(...).instantiate()` 创建实例
3. 先注入依赖
4. 再 `add_child()`

## 推荐写法

```gdscript
var placeholder: InstancePlaceholder = $BotInspector
var inspector: Window = load(placeholder.get_instance_path()).instantiate()
inspector.bot = self
get_tree().root.add_child(inspector)
```

## 为什么这样做

`instantiate()` 只创建对象，不进树。

这样你可以在节点生命周期开始前完成：

- 依赖注入
- 初始状态设置
- 信号绑定

然后再统一 `add_child()`，让 `_ready()` 看到完整状态。

## 路径策略

保留 placeholder，并通过 `get_instance_path()` 动态取资源路径。

这样比硬编码：

```gdscript
preload("res://path.tscn")
```

更稳，因为场景移动后只需要在编辑器里修正 placeholder 引用。

## 何时可以直接 `create_instance()`

只有在下面条件同时满足时才考虑：

- 不需要在进树前注入依赖
- `_ready()` 不依赖外部状态
- 立即替换 placeholder 正是你想要的行为

只要其中一个条件不满足，就回到默认做法。
