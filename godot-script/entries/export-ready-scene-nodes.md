# 导出属性与子节点：须在根/子 `ready` 之后再写入

完整范式（setter-only、省略 getter、不在 `_ready` 重复刷新）见 [scene-property-setter-bridge.md](scene-property-setter-bridge.md)。

## 问题

挂在 **场景（`.tscn`）** 上的脚本里，在根节点 `_ready()` 之前若通过 setter 访问**子节点**（`%` / `get_node` / `@onready` / `_init` 里 `add_child` 的节点），子树可能尚未就绪，导致失败或状态未生效。这不限于 UI——凡是依赖子节点的逻辑都适用。

## 错误示例

```gdscript
@export var title: String = "":
    set(value):
        title = value
        # ❌ 错误：在节点未 ready 时，子节点可能不存在或未就绪
        %Label.text = value
```

## 推荐做法：setter 内 `await ready`，再同步到子节点

导出 setter 里若要**写子节点**，在赋值后使用：

```gdscript
if not is_node_ready():
    await ready
```

再继续访问子节点、发信号等。这样**编辑器里首次写入**与**运行期后续修改**走**同一条路径**。

若子控件还要依赖自身 `_ready()`（例如布局、`custom_minimum_size` 等），再对子节点 `if not btn.is_node_ready(): await btn.ready`。

```gdscript
@onready var title_label: Label = %TitleLabel

@export var title: String = "":
    set(value):
        title = value
        if not is_node_ready():
            await ready
        title_label.text = title
```

逻辑稍长时可抽到私有方法，仍在 setter 里 `await ready` 之后调用。

```gdscript
@onready var foldable_container: FoldableContainer = %FoldableContainer
@onready var title_label: Label = %TitleLabel

@export var title: String = "":
    set(value):
        title = value
        if not is_node_ready():
            await ready
        _apply_title()

func _apply_title() -> void:
    foldable_container.title = title
    title_label.text = title
```

### 多个导出属性

每个 setter 各自 `await ready`（已 ready 时分支几乎无成本），仍共用 `_apply_*` 即可。

```gdscript
@onready var label: Label = %Label
@onready var icon_rect: TextureRect = %Icon

@export var text: String = "":
    set(value):
        text = value
        if not is_node_ready():
            await ready
        label.text = text

@export var icon_texture: Texture2D:
    set(value):
        icon_texture = value
        if not is_node_ready():
            await ready
        icon_rect.texture = icon_texture
```

### `_init` 里 `add_child` 的子节点

与 tscn 子节点相同：根、子都可能未 `ready`，仍用 setter 内 `await ready`，必要时 `await btn.ready`，见上。

## 常见错误

### 在 setter 里直接访问子节点（无任何 ready 等待）

```gdscript
@export var title: String = "":
    set(value):
        title = value
        %Label.text = value  # ❌ 可能在 ready 前执行
```

### 忘记在写子节点前等待 ready

未使用 `if not is_node_ready(): await ready`（及必要的 `await btn.ready`）就访问子节点，与「错误示例」同类问题。

## 为什么重要

- 导出属性可能在场景实例化阶段就被写入（编辑器或代码），早于根或子 `_ready()`。
- `await ready` 把「晚到的」那次赋值在 ready 后继续执行完，一条路径覆盖初始值与后续修改。
- 子节点可以是 tscn 里的控件、`_init` 里创建的按钮等；需要子自身 ready 时再 `await` 子节点即可。
