---
name: general-coding
description: 通用编码技能,审查时必读,编码结束时必读
---

# 通用编码约定

局部变量、循环变量与模式匹配变量禁止单字母或模糊缩写，须能直接看出含义
[rules/naming-full-identifiers.md](rules/naming-full-identifiers.md)

方法命名与参数语义须一一对应，不要让调用方同时承担多种职责或引入可合并的歧义参数
[rules/api-single-semantics.md](rules/api-single-semantics.md)

单函数内只调用一次的逻辑默认内联，同函数多次调用用局部闭包，类级方法仅用于跨函数复用、可测性或明显可读性提升
[rules/local-encapsulation.md](rules/local-encapsulation.md)

默认不新增说明性注释；意图靠命名与结构表达，仅在法规、协议、非常识性坑位等必要时保留最短注释
[rules/minimal-comments.md](rules/minimal-comments.md)

杜绝非必要防御代码：可空用 `T?`、非空用 `T`，契约由类型表达；不在消费处叠冗余判空/长度兜底，风险在入口或边界集中处理
[rules/no-unnecessary-guarding.md](rules/no-unnecessary-guarding.md)

# 维护此文档

在通用编码约定部分增加一句话描述和文档链接，然后在 `rules` 文件夹里新增对应的详细描述
