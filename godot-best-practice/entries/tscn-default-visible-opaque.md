# tscn 默认保持可见、不透明

## 问题

把 `visible = false` 或 `modulate` / `self_modulate` 的 alpha 存进 `.tscn`，场景一打开就看不到这些节点：难以选中、调整布局和核对层级，只能去树里逐个猜。

## 默认做法

`.tscn` 里保存的节点状态一律保持可见、不透明：

- `visible = true`
- `modulate` 与 `self_modulate` 的 alpha 为 `1`

需要隐藏或做淡入淡出的，在运行时处理，不要写进场景默认值。方式不限，例如：

- 在 `_init()` / `_enter_tree()` / `_ready()` 里直接 `hide()`、改 alpha
- 连接 `ready` 或其它信号，在响应里处理
- 由实例化方或上层管理逻辑按业务流程调用
- 交给 `AnimationPlayer` 的首帧或播放动画

以下两种写法最常见。初始化时直接调用：

```gdscript
func _ready() -> void:
	hiddenPanel.hide()
	fadeLayer.modulate.a = 0.0
```

也可以交给信号：本场景内用 `[connection]` 连到 `_on_*`，或由实例化方连本场景根上的信号，在响应里再 `hide()` / 改 alpha。关键是不把隐藏状态存进 `.tscn`。

例如 `Node` 自带的 `ready` 信号：它在 `_ready()` 之后发出，顺序规则与 `_ready()` 相同（子节点先于父节点），此时所有 `@onready` 引用都已就绪。在检视器里把本节点的 `ready` 连到处理函数，就能不写 `_ready()` 完成隐藏：

```text
[connection signal="ready" from="." to="." method="_on_ready"]
```

```gdscript
func _on_ready() -> void:
	hiddenPanel.hide()
```

注意 `ready` 只发一次，且只在首次进树时；离开场景树再回来不会重发，确需重跑时先调用 `request_ready()`。

## 动态的东西都给占位

凡是运行时才确定的东西，`.tscn` 里都应放一个能代表最终效果的占位值，不要留空、留透明或留默认不可见的形态。常见如：

- `icon`、文字、数量、状态
- 贴图：`TextureRect` / `Sprite2D` 给默认贴图
- 模型：`MeshInstance3D` 挂默认 `Mesh`，不要留空 mesh 或缩放到看不见
- 材质 / Shader：给默认材质，不要用全透明材质冒充占位
- `Label` / `Button`：写示例文案，不要留空字符串
- 列表项、卡片：放一个可见的样例子项，运行时复用或按需生成
- 尺寸、位置、颜色等可变值：填一个合理的默认值

占位值只用于编辑期预览尺寸、对齐和层级，运行时再覆盖。空字符串、空资源或全透明贴图会让节点在编辑器里「存在但看不见」，同样不利于编辑。

## 例子

- 弹窗、提示层、遮罩层：场景里可见，`_ready()` 或收到信号时 `hide()`
- 动态头像、图标、名称：场景里放默认图与示例名，运行时替换
- 淡入效果：场景里 alpha 为 1，初始化时再置 0，由动画推回 1
- 仅用于调试显示的节点：同样在初始化时隐藏，或干脆不放进场景

## 不适用

- 节点本身就是「透明容器」的视觉设计（如 `PanelContainer` 无背景色、`Control` 只做布局），这不属于透明度默认值问题
- `@tool` 脚本里按编辑需求临时切换的可见性，不要保存回场景

## 判断标准

打开 `.tscn` 时，理应看到接近运行时首帧的完整布局；若某节点在编辑器里怎么也找不到，先查它的 `visible` 和 `modulate.a` 是否被存进了场景。
