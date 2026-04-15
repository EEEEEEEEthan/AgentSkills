---
name: csharp
description: c#编码技能,审查时必读,初次编码结束准备整理刚才的代码时必读
---

# C# 语法糖

多行原始字符串用 `"""` 定界（C# 11+），结束引号列决定每行去掉的公共前导空白
[entries/csharp11-raw-string.md](entries/csharp11-raw-string.md)

`for (var i = n; i-- > 边界;)` 用后缀自减做递减下标，第三段可空
[entries/for-decrement-loop.md](entries/for-decrement-loop.md)

用 `Enumerable.Range` + `Where` 收集满足条件的下标再随机选，注意中间 `List` 分配与 `Count == 0`
[entries/linq-indices-random.md](entries/linq-indices-random.md)

扩展成员用 `extension (T)` 块（C# 14+）；无额外参数时优先只读属性而非无参方法
[entries/csharp14-extension-members.md](entries/csharp14-extension-members.md)

仅做直通存取且不需要额外逻辑时，优先自动属性；限制外部写入时用 `get; private set;`
[entries/auto-property-preferred.md](entries/auto-property-preferred.md)

无参数、由状态推导的对外值优先只读属性（`public int X => ...`），而不是 `GetX()` 无参方法
[entries/prefer-property-over-parameterless-method.md](entries/prefer-property-over-parameterless-method.md)

可空引用类型（NRT）：可能为空标 `T?` 并在必要处分支；保证非空标 `T` 并用初始化或 `null!` 满足分析器，消费处不写冗余 `!= null`
[entries/csharp-nullable-reference.md](entries/csharp-nullable-reference.md)

# 维护此文档

在「C# 语法糖」部分增加一句话摘要和 `entries/` 链接，在 `entries/` 下新增对应详述；只收短小常用条目，不扩成替代官方文档的教程。
