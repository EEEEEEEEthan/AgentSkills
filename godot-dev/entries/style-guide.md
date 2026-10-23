# GDScript 风格指南

> 正文摘录自 [Godot Engine 4.6 文档 — GDScript style guide](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_styleguide.html)（不含站点导航、页脚、用户评论等）。以下为中文译文。

本风格指南列出编写优雅 GDScript 的约定，旨在鼓励写出干净、可读的代码，并在项目、讨论与教程之间保持一致性，也希望有助于自动格式化工具的发展。

由于 GDScript 接近 Python，本指南借鉴了 Python 的 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 编程风格指南。

风格指南不是死板的教条。有时你无法完全套用下文中的某条规则，此时请自行权衡，并向其他开发者征求意见。

总体而言，在项目和团队内保持风格一致，比逐字逐句照搬本指南更重要。

**说明：** Godot 内置脚本编辑器默认已遵循其中许多约定，可善加利用。

下面是一个遵循本指南的完整类示例：

```gdscript
class_name StateMachine
extends Node
## 玩家的层级状态机。
##
## 初始化状态，并把引擎回调（[method Node._physics_process]、[method Node._unhandled_input]）委托给当前状态。

signal state_changed(previous, new)

@export var initial_state: Node
var is_active = true:
	set = set_is_active

@onready var _state = initial_state:
	set = set_state
@onready var _state_name = _state.name

func _init():
	add_to_group("state_machine")

func _enter_tree():
	print("this happens before the ready method!")

func _ready():
	state_changed.connect(_on_state_changed)
	_state.enter()

func _unhandled_input(event):
	_state.unhandled_input(event)

func _physics_process(delta):
	_state.physics_process(delta)

func transition_to(target_state_path, msg={}):
	if not has_node(target_state_path):
		return

	var target_state = get_node(target_state_path)
	assert(target_state.is_composite == false)

	_state.exit()
	self._state = target_state
	_state.enter(msg)
	Events.player_state_changed.emit(_state.name)

func set_is_active(value):
	is_active = value
	set_physics_process(value)
	set_process_unhandled_input(value)
	set_block_signals(not value)

func set_state(value):
	_state = value
	_state_name = _state.name

func _on_state_changed(previous, new):
	print("state changed")
	state_changed.emit()

class State:
	var foo = 0

	func _init():
		print("Hello!")
```

## 书写格式

### 编码与特殊字符

- 换行使用**换行符（LF）**，不要用 CRLF 或 CR。*（编辑器默认）*
- 每个文件末尾保留**一个**换行符。*（编辑器默认）*
- 使用 **UTF-8** 编码，且不要带 [字节顺序标记（BOM）](https://en.wikipedia.org/wiki/Byte_order_mark)。*（编辑器默认）*
- 缩进使用 **Tab**，不要用空格。*（编辑器默认）*

### 缩进

每一级缩进应比包含它的代码块**多一级**。

**推荐：**

```gdscript
for i in range(10):
	print("hello")
```

**不推荐：**

```gdscript
for i in range(10):
print("hello")

for i in range(10):
		print("hello")
```

续行与**普通代码块**区分开时，应使用 **2 级**缩进。

**推荐：**

```gdscript
effect.interpolate_property(sprite, "transform/scale",
		sprite.get_scale(), Vector2(2.0, 2.0), 0.3,
		Tween.TRANS_QUAD, Tween.EASE_OUT)
```

**不推荐：**

```gdscript
effect.interpolate_property(sprite, "transform/scale",
	sprite.get_scale(), Vector2(2.0, 2.0), 0.3,
	Tween.TRANS_QUAD, Tween.EASE_OUT)
```

**例外：** 数组、字典与枚举的续行只用 **1 级**缩进区分。

**推荐：**

```gdscript
var party = [
	"Godot",
	"Godette",
	"Steve",
]

var character_dict = {
	"Name": "Bob",
	"Age": 27,
	"Job": "Mechanic",
}

enum Tile {
	BRICK,
	FLOOR,
	SPIKE,
	TELEPORT,
}
```

**不推荐：**

```gdscript
var party = [
		"Godot",
		"Godette",
		"Steve",
]

var character_dict = {
		"Name": "Bob",
		"Age": 27,
		"Job": "Mechanic",
}

enum Tile {
		BRICK,
		FLOOR,
		SPIKE,
		TELEPORT,
}
```

### 末尾逗号

在数组、字典、枚举的**最后一行**也写逗号。这样在重构、以及在版本控制里追加元素时 diff 更干净，不必改到「原最后一行」。

**推荐：**

```gdscript
var array = [
	1,
	2,
	3,
]
```

**不推荐：**

```gdscript
var array = [
	1,
	2,
	3
]
```

**单行**列表不需要末尾逗号，不要加。

**推荐：**

```gdscript
var array = [1, 2, 3]
```

**不推荐：**

```gdscript
var array = [1, 2, 3,]
```

### 空行

函数与类定义的前后各留 **两行** 空行：

```gdscript
func heal(amount):
	health += amount
	health = min(health, max_health)
	health_changed.emit(health)


func take_damage(amount, effect=null):
	health -= amount
	health = max(0, health)
	health_changed.emit(health)
```

函数内部用 **一行** 空行分隔逻辑块。

**说明：** 在类参考与文档中的短代码片段里，类与函数之间有时只空一行。

### 行宽

单行代码尽量不超过 **100** 个字符。

若可以，尽量压在 **80** 以内，便于小屏阅读或在外部编辑器里并排打开两个脚本，也方便看 diff。

### 一行一句

不要把多条语句写在同一行（含条件语句），以利于阅读。

**推荐：**

```gdscript
if position.x > width:
	position.x = 0

if flag:
	print("flagged")
```

**不推荐：**

```gdscript
if position.x > width: position.x = 0

if flag: print("flagged")
```

**唯一例外**是三目运算符：

```gdscript
next_state = "idle" if is_on_floor() else "fall"
```

### 多行书写以提升可读性

很长的 `if` 或嵌套三目表达式，拆成多行更易读。续行仍是同一表达式的一部分，因此要用 **2 级**缩进，而不是 1 级。

GDScript 可用括号或反斜杠折行。本指南**更推荐括号**，重构更方便；反斜杠折行需保证最后一行末尾没有反斜杠；用括号则无此顾虑。

条件表达式折行时，`and` / `or` 应放在**续行开头**，而不是上一行末尾。

**推荐：**

```gdscript
var angle_degrees = 135
var quadrant = (
		"northeast" if angle_degrees <= 90
		else "southeast" if angle_degrees <= 180
		else "southwest" if angle_degrees <= 270
		else "northwest"
)

var position = Vector2(250, 350)
if (
		position.x > 200 and position.x < 400
		and position.y > 300 and position.y < 400
):
	pass
```

**不推荐：**

```gdscript
var angle_degrees = 135
var quadrant = "northeast" if angle_degrees <= 90 else "southeast" if angle_degrees <= 180 else "southwest" if angle_degrees <= 270 else "northwest"

var position = Vector2(250, 350)
if position.x > 200 and position.x < 400 and position.y > 300 and position.y < 400:
	pass
```

### 避免多余括号

表达式与条件里不要无故加括号；除非为了运算顺序或多行折行，否则只会降低可读性。

**推荐：**

```gdscript
if is_colliding():
	queue_free()
```

**不推荐：**

```gdscript
if (is_colliding()):
	queue_free()
```

### 布尔运算符

优先使用英文单词形式，可读性最好：

- 用 `and`，不要用 `&&`。
- 用 `or`，不要用 `||`。
- 用 `not`，不要用 `!`。

若表达式较长，可用括号消除歧义。

**推荐：**

```gdscript
if (foo and bar) or not baz:
	print("condition is true")
```

**不推荐：**

```gdscript
if foo && bar || !baz:
	print("condition is true")
```

### 注释与空格

普通注释（`#`）与文档注释（`##`）在 `#` 后应有一个空格；**被注释掉的代码**则不要多空格。区域注释（`#region` / `#endregion`）语法固定，**不要**在 `#` 后加空格。

这样便于区分「说明文字」与「临时禁用的代码」。

**推荐：**

```gdscript
# 这是一条注释。
#print("这是被注释掉的代码")
```

**不推荐：**

```gdscript
#这是一条注释。
# print("这是被注释掉的代码")
```

**说明：** 在脚本编辑器中，对选中代码切换注释可按 **Ctrl + K**，会在各行代码前加/删一个 `#`。

长说明尽量**独占一行**；行尾注释只宜很短，通常几个词即可。

**推荐：**

```gdscript
# 若写成行尾注释会让下一行过长，应像这样单独成行。
print("Example") # 短注释。
```

**不推荐：**

```gdscript
print("Example") # 若写成行尾注释会让本行过长，不推荐。
```

### 空白

运算符两侧、逗号后各留 **一个** 空格；字典下标与函数调用里不要多余空格。**单行字典**在 `{` 后与 `}` 前各留一空格，便于与数组 `[]` 区分（不少字体里 `[]` 与 `{}` 容易混）。

**推荐：**

```gdscript
position.x = 5
position.y = target_position.y + 10
dict["key"] = 5
my_array = [4, 5, 6]
my_dictionary = { key = "value" }
print("foo")
```

**不推荐：**

```gdscript
position.x=5
position.y = mpos.y+10
dict ["key"] = 5
myarray = [4,5,6]
my_dictionary = {key = "value"}
print ("foo")
```

不要用空格做**竖向对齐**：

```gdscript
x = 100
y = 100
velocity = 500
```

### 引号

默认用**双引号**；若用单引号能少写转义，则可用单引号。例如：

```gdscript
# 普通字符串。
print("hello world")

# 一般仍用双引号，避免转义。
print("hello 'world'")

# 例外：用单引号包住双引号，减少转义。
print('hello "world"')

# 两种都要两次转义时，仍以双引号为优先。
print("'hello' \"world\"")
```

### 数字

浮点数不要省略**前导 0** 或**末尾 .0**，否则不易一眼区分整型与浮点。

**推荐：**

```gdscript
var float_number = 0.234
var other_float_number = 13.0
```

**不推荐：**

```gdscript
var float_number = .234
var other_float_number = 13.
```

十六进制中的字母用小写，更易读。

**推荐：**

```gdscript
var hex_number = 0xfb8c0b
```

**不推荐：**

```gdscript
var hex_number = 0xFB8C0B
```

大数字可使用 GDScript 字面量中的下划线 `_` 分组。

**推荐：**

```gdscript
var large_number = 1_234_567_890
var large_hex_number = 0xffff_f8f8_0000
var large_bin_number = 0b1101_0010_1010
# 小于 1000000 的数一般不必加分隔符。
var small_number = 12345
```

**不推荐：**

```gdscript
var large_number = 1234567890
var large_hex_number = 0xfffff8f80000
var large_bin_number = 0b110100101010
# 小于 1000000 的数一般不必加分隔符。
var small_number = 12_345
```

## 命名约定

以下命名与 Godot 引擎内置风格一致；若违背，容易与引擎 API「打架」，整体观感也不统一。汇总表：

| 类型 | 约定 | 示例 |
| --- | --- | --- |
| 文件名 | snake_case | `yaml_parser.gd` |
| 类名 | PascalCase | `class_name YAMLParser` |
| 节点名 | PascalCase | `Camera3D`, `Player` |
| 函数 | snake_case | `func load_level():` |
| 变量 | snake_case | `var particle_effect` |
| 信号 | snake_case | `signal door_opened` |
| 常量 | CONSTANT_CASE | `const MAX_SPEED = 200` |
| 枚举名 | PascalCase | `enum Element` |
| 枚举成员 | CONSTANT_CASE | `{EARTH, WATER, AIR, FIRE}` |

### 文件名

文件名用 snake_case。若脚本带 `class_name`，文件名由 PascalCase 类名转为 snake_case：

```gdscript
# 文件应保存为 weapon.gd。
class_name Weapon
extends Node
```

```gdscript
# 文件应保存为 yaml_parser.gd。
class_name YAMLParser
extends Object
```

这与 Godot 源码中 C++ 文件命名一致，也减少从 Windows 导出到其他平台时的大小写问题。

### 类与节点

类名、节点名用 PascalCase：

```gdscript
extends CharacterBody3D
```

`preload` 等到常量/变量里的**类**也用 PascalCase：

```gdscript
const Weapon = preload("res://weapon.gd")
```

### 函数与变量

函数与变量名用 snake_case：

```gdscript
var particle_effect
func load_level():
	pass
```

用户必须覆写的虚方法、私有函数、私有成员名前加**一个**下划线 `_`：

```gdscript
var _counter = 0
func _recalculate_path():
	pass
```

### 信号

信号名用**过去时**：

```gdscript
signal door_opened
signal score_changed
```

### 常量与枚举

常量用 CONSTANT_CASE（全大写，单词间 `_`）：

```gdscript
const MAX_SPEED = 200
```

枚举**类型名**用 PascalCase，且用**单数**；**成员**用 CONSTANT_CASE（视作常量）：

```gdscript
enum Element {
	EARTH,
	WATER,
	AIR,
	FIRE,
}
```

每个枚举成员**独占一行**，便于在上方写文档注释，版本 diff 也更干净。

**推荐：**

```gdscript
enum Element {
	EARTH,
	WATER,
	AIR,
	FIRE,
}
```

**不推荐：**

```gdscript
enum Element { EARTH, WATER, AIR, FIRE }
```

## 代码顺序

本节只讲**声明顺序**。书写格式见 [书写格式](#书写格式)；命名见 [命名约定](#命名约定)。

建议按以下顺序组织 GDScript：

1. `@tool`、`@icon`、`@static_unload`
2. `class_name`
3. `extends`
4. 文档注释（`##`）
5. signals
6. enums
7. constants
8. static 变量
9. `@export` 变量
10. 其余普通成员变量
11. `@onready` 变量
12. `_static_init()`
13. 其余 static 方法
14. 覆写的**内置虚方法**：
	1. `_init()`
	2. `_enter_tree()`
	3. `_ready()`
	4. `_process()`
	5. `_physics_process()`
	6. 其余虚方法
15. 覆写的自定义方法
16. 其余方法
17. 内部类（inner classes）

同一类内再按**访问级别**：

1. public
2. private

这样从上到下阅读更顺，新手也更容易理解依赖关系，减少「声明顺序导致」的错误。

四条经验法则：

1. 属性与信号在前，方法在后。
2. public 在 private 前。
3. 虚回调在类的对外接口之前。
4. 构造/初始化（`_init`、`_ready`）在运行时修改对象状态的方法之前。

### 类声明

若要在编辑器中运行，把 `@tool` 放在脚本**第一行**。

接着可选 `@icon`，再按需写 `class_name`（全局类型注册见 [Registering named classes](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_basics.html#doc-gdscript-basics-class-name)）。若为 [抽象类](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_basics.html#doc-gdscript-basics-abstract-class)，在 `class_name` **之前**加 `@abstract`。

然后写 `extends`（若继承内置类型）。

之后可写类的可选 [文档注释](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_documentation_comments.html#doc-gdscript-documentation-comments)，说明职责、用法等。

```gdscript
@abstract
class_name MyNode
extends Node
## 简要说明类的职责与功能。
##
## 脚本能做什么、其他开发者应如何使用等。
```

内部类可用**单行**声明：

```gdscript
## 简要说明类的职责与功能。
##
## 脚本能做什么、其他开发者应如何使用等。
@abstract class MyNode extends Node:
	pass
```

### 信号与属性

文档注释之后先写 signal，再写成员变量（属性）。

枚举紧跟 signal，因为可作为其他属性的 `@export` 提示类型。

再依次：常量、`@export`、公开变量、私有变量、`@onready`。

```gdscript
signal player_spawned(position)

enum Job {
	KNIGHT,
	WIZARD,
	ROGUE,
	HEALER,
	SHAMAN,
}

const MAX_LIVES = 3

@export var job: Job = Job.KNIGHT
@export var max_health = 50
@export var attack = 5

var health = max_health:
	set(new_health):
		health = new_health

var _speed = 300.0

@onready var sword = get_node("Sword")
@onready var gun = get_node("Gun")
```

**说明：** `@onready` 在 `_ready` 之前求值，可用来缓存场景中本类依赖的子节点；上例即此意。

### 成员变量

若某数据只在某个方法内使用，不要提成成员变量，否则难读；应改为方法内的局部变量。

### 局部变量

局部变量尽量靠近**首次使用**处声明，减少上下翻动。

### 方法与静态函数

属性之后写方法。

先 `_init()`（对象在内存中创建时调用），再 `_ready()`（节点进入场景树时调用），以体现初始化流程。

接着是其他内置虚回调（如 `_unhandled_input()`、`_physics_process()`），表示主循环与引擎交互。

再写类的其余接口：先 public，后 private。

```gdscript
func _init():
	add_to_group("state_machine")

func _ready():
	state_changed.connect(_on_state_changed)
	_state.enter()

func _unhandled_input(event):
	_state.unhandled_input(event)

func transition_to(target_state_path, msg={}):
	if not has_node(target_state_path):
		return

	var target_state = get_node(target_state_path)
	assert(target_state.is_composite == false)

	_state.exit()
	self._state = target_state
	_state.enter(msg)
	Events.player_state_changed.emit(_state.name)

func _on_state_changed(previous, new):
	print("state changed")
	state_changed.emit()
```

## 静态类型

GDScript 支持 [可选静态类型](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/static_typing.html#doc-gdscript-static-typing)。

### 显式标注类型

变量类型用冒号 `:`：

```gdscript
var health: int = 0
```

函数返回值用 `->`：

```gdscript
func heal(amount: int) -> void:
	pass
```

### 类型推断

多数情况可用 `:=` 让编译器推断。若类型与赋值写在**同一行**，优先 `:=`；否则优先写显式类型。

**推荐：**

```gdscript
# 可能是 int 或 float，应显式写出。
var health: int = 0

# 明显是 Vector3，可用 :=。
var direction := Vector3(1, 2, 3)
```

类型模糊时要写类型；类型多余时可省略标注。

**不推荐：**

```gdscript
# 被标成 int，但本意可能是 float。
var health := 0

# 类型信息重复。
var direction: Vector3 = Vector3(1, 2, 3)

# 读者一眼看不出类型。
var value := complex_function()
```

有时必须显式标注，否则编译器只能按函数返回的宽类型推断，行为会不符合预期。例如 `get_node()` 在相关场景/文件未载入时无法推断为具体节点类型，应显式写出。

**推荐：**

```gdscript
@onready var health_bar: ProgressBar = get_node("UI/LifeBar")
```

**不推荐：**

```gdscript
# 无法推断为 ProgressBar，会退成 Node。
@onready var health_bar := get_node("UI/LifeBar")
```

也可用 `as` 转换返回值，再据此推断变量类型：

```gdscript
@onready var health_bar := get_node("UI/LifeBar") as ProgressBar
# health_bar 的类型为 ProgressBar
```

**说明：** 相对类型标注，这种方式在类型上更「[安全](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/static_typing.html#doc-gdscript-static-typing-safe-lines)」，但若运行时类型不匹配会**静默**变成 `null`，空安全较差，且不一定报错/警告。
