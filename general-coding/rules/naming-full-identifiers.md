# 约定：标识符完整命名

## 范围

除下文「局部变量」专节外，**所有**出现在源码中的命名（成员字段、属性、参数、枚举成员、类型级常量等）均适用完整命名，无例外。

## 成员与 API 命名

- **禁止**在字段、属性、参数中使用单字母、数学符号式缩写或模糊缩写（如 `_p0`、`_m0`、`_elapsed`、`p1`、`m1`）。
- 命名须能直接看出含义与单位/坐标系；需要消歧时加前缀或后缀（如 `world_position`、`elapsed_seconds`、`start_tangent`），不要用协议或公式里的简写代替业务语义。
- 私有字段用 `_` 前缀时，`_` 之后仍须完整词组，不得把 `_` 当作允许缩写的理由。

### 不符合

```gdscript
var _p0: Vector2
var _m0: Vector2
var _elapsed: float

func _hermite_position(u: float, p0: Vector2, m0: Vector2, p1: Vector2, m1: Vector2) -> Vector2:
```

### 符合

```gdscript
var _attract_start_world_position: Vector2
var _attract_start_tangent: Vector2
var _attract_elapsed_seconds: float

func _hermite_position(
		normalized_u: float,
		start_position: Vector2,
		start_tangent: Vector2,
		end_position: Vector2,
		end_tangent: Vector2,
) -> Vector2:
```

## 局部变量

- **禁止**在局部变量、循环变量、模式匹配变量中使用单字母或模糊缩写。
- 命名须能直接看出含义，例如：当前节点用 `node`/`control`，子节点用 `child`，若需类型区分用 `childControl`、`childNode`；容器用 `container`，不要用 `n`、`cc`、`cont`、`p` 等。

### 不符合

```csharp
var n = stack.Pop();
if (child is Control cc) processStack.Push(cc);
```

### 符合

```csharp
var node = stack.Pop();
if (child is Control childControl) processStack.Push(childControl);
```
