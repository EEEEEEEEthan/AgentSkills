# 场景嵌入脚本（Embedded Script）

## 默认策略

**新脚本能嵌入就用嵌入**：在场景里给节点挂脚本，让 Godot 把源码写进 `.tscn` 的 `[sub_resource type="GDScript"]` / `script/source`，而不是先建独立的 `.gd` 文件。

嵌入脚本适合「只服务这一个场景」的胶水逻辑：转发信号、同步 UI、少量协调代码（例如 `main.tscn`、`control_window.tscn` 里那种）。

## 何时才拆成独立 `.gd`

| 继续嵌入 | 拆出 `.gd` |
|----------|------------|
| 仅本场景使用 | 多个场景复用同一脚本 |
| 体量小、职责单一 | 逻辑已大到 `.tscn` diff 难读 |
| 不需要 `class_name` 被别处引用 | 需要 `class_name`、Autoload 或跨场景强类型 |
| | 要单独做版本管理 / 大规模重构（可选） |

拆分时在编辑器里用「解除脚本关联并保留实例数据」，避免手改路径弄断连接。

## 写法约定

### 1. `extends` 与挂载节点一致

脚本挂在哪个节点上，`extends` 就写该节点类型（`Window`、`CheckButton` 等），不要为省事写成更泛的基类。

### 2. 参数名不要遮蔽引擎成员

信号参数、回调参数**禁止**与当前脚本所在类型（及其祖先）的**属性/方法同名**，否则易出现解析错误，例如 `Expected expression as the function argument`：

```gdscript
# 错误：Window / Node 上已有 scale、visible 等
signal scale_changed(scale: int)
func _on_scale_changed(scale: int) -> void: ...

# 正确
signal scale_changed(new_scale: int)
func _on_scale_changed(new_scale: int) -> void: ...
```

常见冲突名：`scale`、`visible`、`position`、`size`、`name`、`rotation`、`modulate` 等。信号侧与接收侧改名保持一致即可，连接不依赖参数名。

### 3. 嵌入源码里的字符串引号必须转义

`script/source = "..."` 整块由 `.tscn` 的双引号包裹，脚本里的 `"` 必须写成 `\"`，否则提前截断字符串，报 `Expected expression as the function argument` 等怪错（行号常不准）。

```gdscript
# .tscn 里应写成（注意 \"）
var game := %Game.get_node(\"Game\") as Game
_control_window = get_tree().current_scene.get_node(^\"ControlWindow\") as Window
```

在 Godot 脚本编辑器里改嵌入脚本时，保存场景会自动转义；**手改 `.tscn` 正文时务必检查 `\"`**。

同场景 unique 名仍可用 `%`，无需引号。

### 4. 信号连接写在场景里

同一 `.tscn` 内发射端、接收端都已存在的静态连接，用检视器连好并保留 `[connection ...]`，见 [scene-signals-inspector.md](scene-signals-inspector.md)。嵌入脚本只写槽函数，不在 `_ready()` 里重复 `connect`。

### 5. 一个节点一段嵌入逻辑

子节点若只有一行转发（如 `CheckButton` 把 `toggled` 交给 `owner`），可以单独再挂一小段嵌入脚本；不要为同一节点混用「根场景一个大 `.gd` + 子节点嵌入」除非职责清晰。

### 6. 避免在嵌入脚本里堆「系统级」逻辑

存档、地图生成、可复用数据类仍放独立 `.gd`（如 `game.gd`）。嵌入脚本只做本场景的编排与 UI。

## 维护注意

- 改嵌入源码后保存场景；合并冲突时关注 `script/source` 多行字符串块。
- 字符串里的 `"` 在 `.tscn` 里会转义，**优先在 Godot 脚本编辑器里改**，少手改 `.tscn` 正文。
- 嵌入脚本一般**不加** `class_name`；跨场景访问用场景结构、`get_node` 或显式类型转换（`as Game`）。

## 与本仓库的对应关系

| 场景 | 做法 |
|------|------|
| `main.tscn` | 根节点嵌入：连接 ControlWindow / GameWindow |
| `control_window.tscn` | 根 `Window` + 子 `CheckButton` 各一段嵌入 |
| `game/game.gd` | 独立文件：可复用、`class_name Game` |
