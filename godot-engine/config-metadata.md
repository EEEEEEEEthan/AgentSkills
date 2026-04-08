# 场景关键引用放到子节点 Metadata

## 问题

关键 `PackedScene` 或资源引用如果只放在根节点普通 `@export` 上，协作编辑和场景合并时更容易被误改。

## 默认做法

为“不应被随便改掉”的引用创建专用子节点，常用名是 `Config`，再把引用写到这个子节点的 Metadata 上。

## 推荐写法

```gdscript
const META_BULLET_SCENE := "bullet_scene"

func _ready() -> void:
	var config: Node = get_node("Config")
	var bullet: PackedScene = config.get_meta(META_BULLET_SCENE) as PackedScene
```

## 这样做的好处

- 引用和节点结构绑在一起，更容易理解
- diff 时更容易看出是谁改了关键配置
- 场景移动或局部改造时，误伤概率更低

## 额外建议

- 可以给 `Config` 设 `process_mode = PROCESS_MODE_DISABLED`
- 若代码侧需要兜底，可在 `_ready()` 里检查 `has_meta()`

## 不适用

如果该引用本来就需要频繁在检视器里拖拽替换，而且误改成本很低，普通 `@export` 依然可以用。
