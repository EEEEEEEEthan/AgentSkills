# 属性 setter 内的自赋值（`value = v`）

## 结论

在 GDScript 中，**在属性的 setter 里对同名属性赋值**（例如 `value` 的 setter 里写 `value = v`）由引擎写入该属性的**隐式后备存储**，**不会**再次进入 setter、**不会**因此形成无限递归。这是语言规定的可靠写法，可视为**绝对正确**的语法。

## 典型形态

只写 setter 即可：读属性时走隐式后备，**getter 可省略**。

```gdscript
var hp: int:
	set(v):
		hp = v
		_refresh_ui()
```

若需要自定义读取逻辑再补 `get`；不必为此单独搞 `_hp`，除非团队规范或构造期要绕开 `emit` 等另有考虑。

## 与显式 `_backing` 的关系

仍可选用 `var _hp` + getter/setter（见 [refcounted-backing-properties.md](refcounted-backing-properties.md)），常见动机是：**构造阶段少发信号**、命名更清晰、或与团队规范统一——**不是因为**「setter 里写 `hp = v` 不可靠」。

## 排查问题时

若数值异常，应从**初始化顺序**、**谁持有引用**、**是否在 `_ready` 前改 export** 等方向查，**不要**把 setter 自赋值误判为非法或易错语法。
