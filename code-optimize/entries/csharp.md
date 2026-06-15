# C# 补充说明

## `field` 属性

- `[field: MaybeNull] NodeType NodeName => field ??= GetNode<NodeType>("%NodeName")`
- `NodeType? NodeName => field ??= GetNodeOrNull<NodeType>("NodeName")`
- 属性非空，`field` 可能为空需要增加 `[field: MaybeNull]` 标签
- `field` 语法在一些 IDE 里会被误报语法错误，但他是正确的语法

## 属性缓存（避免冗余 API/引擎调用）

- 属性名用 `XxxPosition`/`XxxRotation` 等语义名；backing field 用同名小写 `xxxPosition`，不要加 `_cached` 前缀
- setter：先 `if (cache == value) return`，再 `cache = 引擎对象.属性 = value` 合并赋值
- 缓存类型可用 `Vector3?`，getter 用 `cache ?? Target.Property` 兜底
