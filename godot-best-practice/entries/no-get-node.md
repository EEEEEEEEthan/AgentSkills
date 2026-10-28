# 禁止 `get_node` 字符串路径

## 坑

`get_node("LeftHand")`、`owner.get_node("Game/Coffee")` 把场景结构写成字符串。改名、挪层级时编译器不报错，运行才断。

## 正确做法

- 本场景里的节点：给它勾上唯一名，用 `%Coffee`。
- 别的场景里的节点：调用对方场景根的公开 API，例如 `Character.left_hand`、`left_target_global_position`、`Hand`、`Coffee`。不要把 `"LeftHand"` 这种路径写进代码。

```gdscript
# ❌
_left_hand = _character.get_node("LeftHand") as Hand
_coffee = owner.get_node("Game/Coffee") as Coffee

# ✅
_left_hand = _character.left_hand
_coffee = %Coffee
```
