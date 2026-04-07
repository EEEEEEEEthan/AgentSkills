---
name: godot-script
description: Godot 脚本编写最佳实践
---

# Godot 脚本最佳实践

本文档包含 Godot 脚本编写的核心原则和最佳实践，确保代码正确、高效、易于调试。

## 核心原则

### 1. 正确处理节点初始化时机

**问题**：在 `_ready()` 之前设置属性时，子节点可能还不存在，导致访问失败或更新无效。

**错误示例**：
```gdscript
@export var title: String = "":
    set(value):
        title = value
        # ❌ 错误：在节点未 ready 时，子节点可能不存在
        %Label.text = value
```

**正确做法**：
```gdscript
@export var title: String = "":
    set(value):
        title = value
        # ✅ 正确：只在节点 ready 后更新 UI
        if is_node_ready():
            _refresh_title()

func _ready():
    # ✅ 在 _ready() 中统一刷新所有属性
    _refresh_title()

func _refresh_title():
    title_label.text = title
```

**为什么重要**：
- 属性可能在场景加载时就被设置（通过编辑器或代码）
- 此时子节点可能还未初始化，直接访问会失败
- 在 `_ready()` 中统一刷新确保所有属性都能正确应用到 UI

### 2. 使用 @onready 缓存节点引用

**问题**：使用 `%` 符号每次查找节点，性能差且代码不清晰。

**错误示例**：
```gdscript
func _refresh_title():
    var label = %TitleLabel  # ❌ 每次调用都查找节点
    label.text = title
```

**正确做法**：
```gdscript
@onready var title_label: Label = %TitleLabel  # ✅ 在 _ready() 时缓存

func _refresh_title():
    title_label.text = title  # ✅ 直接使用缓存的引用
```

**为什么重要**：
- `@onready` 在 `_ready()` 时自动初始化，性能更好
- 代码更清晰，明确表达节点依赖关系
- 类型提示让 IDE 能提供更好的代码补全和检查

### 3. 子节点访问场景根：用 owner 而非 get_parent()

**问题**：子节点需要访问场景根（如 BotMain）时，用 `get_parent()` 会随层级变动而失效。

**错误示例**：
```gdscript
# State 是 Bot 的子节点，需要访问 BotMain
var bot_main = get_parent()  # ❌ 若 State 移到 StateMachine 下，parent 就变了
```

**正确做法**：
```gdscript
var bot_main = owner as Node2D  # ✅ owner 始终指向场景根，层级重构不受影响
```

**何时用**：子节点/组件需要访问所属场景的根节点时。

### 4. 避免不必要的防御性代码

**问题**：对 unique 节点添加 null 检查会掩盖问题，让调试变得困难。

**错误示例**：
```gdscript
func _refresh_title():
    var label = %TitleLabel
    if label:  # ❌ 错误：unique 节点应该始终存在
        label.text = title
```

**正确做法**：
```gdscript
@onready var title_label: Label = %TitleLabel

func _refresh_title():
    title_label.text = title  # ✅ 直接访问，如果不存在会立即报错
```

**为什么重要**：
- unique 节点在场景中应该始终存在
- 如果不存在，应该立即报错而不是静默失败
- 防御性代码会隐藏问题，让 bug 更难发现和修复
- 直接访问让问题在开发阶段就能暴露

**例外情况**：
- 如果节点确实可能不存在（非 unique 节点），可以保留检查
- 但应该使用 `get_node_or_null()` 并明确处理 null 情况

### 4. 成员声明顺序

**原则**：字段 → 属性（含 getter/setter）→ 方法

**正确示例**：
```gdscript
var _move_task: BotTaskMove
var _cancel_flag: RefCounted

var is_cancelled: bool:
	get: return _move_task.aborted

func _ready() -> void:
	pass
```

**为什么重要**：统一顺序便于快速定位，属性依赖字段，方法依赖两者。

### 5. 返回值风格：属性 vs 方法

**原则**：
- **返回固定值**：优先用属性（getter），如 `var is_cancelled: bool: get: return _move_task.aborted`
- **每次获取新实例**：避免命名为 `get_xxx`，用 `new_xxx` 等，如 `new_bot_api()` 而非 `get_bot_api()`

**为什么重要**：`get_xxx` 易被误解为返回缓存引用；属性更符合“读取状态”的语义。

### 6. 惰性资源：getter 与缓存成员同名（与 `audio_stream_beep` 一致）

**原则**：懒加载 `AudioStream` / `Resource` 时，用**一条**与语义对应的 `var audio_stream_xxx`（或同类命名），在 getter 里 `if not audio_stream_xxx` 再加载并 `return audio_stream_xxx`，与项目中 `audio_stream_beep` 写法一致。

**正确示例**：
```gdscript
var audio_stream_selection: AudioStream:
	get:
		if not audio_stream_selection:
			audio_stream_selection = _load_audio_stream(&"res://audios/selection.wav")
		return audio_stream_selection
```

**禁止**：在「选项 A」的 getter 里用「选项 B」的成员做 `if not` 或赋值（例如 selection 的 getter 里误写 `audio_stream_beep`），否则会在 B 已加载后永远不加载 A。

**不推荐**：为同一资源再拆 `_backing` 字段，除非有明确理由；本仓库优先上述同名惰性成员风格。

### 7. call_deferred 使用 StringName

**问题**：`call_deferred("method_name", args)` 使用字符串字面量，易拼写错误且无类型提示。

**正确做法**：
```gdscript
# ✅ 使用 & 前缀生成 StringName，Godot 4 推荐用于方法名
object.call_deferred(&"move_by", direction, callback)
```

**为什么重要**：
- StringName 是 Godot 4 中方法名的推荐类型
- `call_deferred` 必须传入方法名，无法直接传 Callable

## 实践模式

### 标准模式：导出属性 + 刷新函数

```gdscript
extends PanelContainer

# 1. 使用 @onready 缓存所有需要的节点
@onready var foldable_container: FoldableContainer = %FoldableContainer
@onready var title_label: Label = %TitleLabel

# 2. 导出属性，setter 只在 ready 后更新 UI
@export var title: String = "":
    set(value):
        title = value
        if is_node_ready():
            _refresh_title()

# 3. 在 _ready() 中统一刷新所有属性
func _ready():
    _refresh_title()

# 4. 独立的刷新函数，直接访问节点（无防御代码）
func _refresh_title():
    foldable_container.title = title
    title_label.text = title
```

### 多个属性的模式

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

## 检查清单

编写 Godot 脚本时，检查：

- [ ] 成员顺序是否为：字段 → 属性 → 方法？
- [ ] 导出属性的 setter 是否检查 `is_node_ready()`？
- [ ] 是否在 `_ready()` 中刷新所有导出属性？
- [ ] 是否使用 `@onready` 缓存所有节点引用？
- [ ] 子节点访问场景根时是否用 `owner` 而非 `get_parent()`？
- [ ] 是否移除了对 unique 节点的防御性检查？
- [ ] 刷新函数是否直接访问节点（无 null 检查）？
- [ ] 节点引用是否有正确的类型提示？
- [ ] 惰性加载资源是否采用「成员与 getter 同名」且每项只判断自己的成员？
- [ ] `call_deferred` 是否使用 `&"method_name"` 而非 `"method_name"`？

## 常见错误

### 错误 1：忘记在 _ready() 中刷新

```gdscript
@export var title: String = "":
    set(value):
        title = value
        if is_node_ready():
            _refresh_title()

# ❌ 错误：缺少 _ready() 中的刷新
# 如果属性在场景中设置了初始值，不会更新到 UI
```

### 错误 2：在 setter 中直接访问节点

```gdscript
@export var title: String = "":
    set(value):
        title = value
        %Label.text = value  # ❌ 错误：可能在 ready 前调用
```

### 错误 3：使用 % 符号而不是 @onready

```gdscript
func _refresh():
    var label = %Label  # ❌ 错误：每次调用都查找
    label.text = text
```

### 错误 4：不必要的防御性代码

```gdscript
func _refresh():
    var label = %Label
    if label:  # ❌ 错误：unique 节点应该始终存在
        label.text = text
```

### 错误 5：call_deferred 使用字符串字面量

```gdscript
object.call_deferred("move_by", direction, callback)  # ❌ 应使用 &"move_by"
```

### 错误 5：用 get_parent() 访问场景根

```gdscript
# 子节点需要访问 BotMain
var bot_main = get_parent()  # ❌ 层级变动（如移到 StateMachine 下）会失效
```

应使用 `owner as Node2D`。

## 总结

遵循这些原则可以：
- ✅ 确保属性在任何时机设置都能正确更新 UI
- ✅ 提高代码性能（缓存节点引用）
- ✅ 子节点访问场景根时层级重构不受影响（owner）
- ✅ 让问题更容易暴露和调试
- ✅ 代码更清晰、更易维护
