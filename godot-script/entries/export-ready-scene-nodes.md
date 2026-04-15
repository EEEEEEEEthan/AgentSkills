# 导出属性与场景子节点：须在 `_ready()` / `is_node_ready()` 之后访问

## 问题

挂在 **场景（`.tscn`）** 上的脚本里，在 `_ready()` 之前若通过 setter 访问**子节点**（`%` / `get_node` / `@onready` 所指的节点），子树可能尚未就绪，导致失败或状态未生效。这不限于 UI——凡是依赖场景里子节点的逻辑都适用。

## 错误示例

```gdscript
@export var title: String = "":
    set(value):
        title = value
        # ❌ 错误：在节点未 ready 时，子节点可能不存在
        %Label.text = value
```

## 正确做法

```gdscript
@export var title: String = "":
    set(value):
        title = value
        # ✅ 正确：只在场景子节点就绪后再同步
        if is_node_ready():
            _refresh_title()

func _ready():
    # ✅ 在 _ready() 中统一把导出值应用到子节点
    _refresh_title()

func _refresh_title():
    title_label.text = title
```

## 实践：标准模式（导出 + 刷新函数）

```gdscript
extends PanelContainer

@onready var foldable_container: FoldableContainer = %FoldableContainer
@onready var title_label: Label = %TitleLabel

@export var title: String = "":
    set(value):
        title = value
        if is_node_ready():
            _refresh_title()

func _ready():
    _refresh_title()

func _refresh_title():
    foldable_container.title = title
    title_label.text = title
```

## 实践：多个导出属性

```gdscript
extends Control

@onready var label: Label = %Label
@onready var icon: TextureRect = %Icon

@export var text: String = "":
    set(value):
        text = value
        if is_node_ready():
            _refresh_text()

@export var icon_texture: Texture2D:
    set(value):
        icon_texture = value
        if is_node_ready():
            _refresh_icon()

func _ready():
    _refresh_text()
    _refresh_icon()

func _refresh_text():
    label.text = text

func _refresh_icon():
    icon.texture = icon_texture
```

## 常见错误

### 忘记在 `_ready()` 中刷新

若缺少 `_ready()` 里对 `_refresh_*` 的调用，场景中设置的初始导出值不会同步到子节点。

### 在 setter 里直接访问子节点

```gdscript
@export var title: String = "":
    set(value):
        title = value
        %Label.text = value  # ❌ 可能在 ready 前执行
```

## 为什么重要

- 导出属性可能在场景实例化阶段就被写入（编辑器或代码），早于子节点 `_ready()`。
- 在 `_ready()` 中统一「应用到子节点」，能保证初始值与后续 setter 行为一致；子节点可以是控件、碰撞体、占位符实例化结果等任意 tscn 内容。
