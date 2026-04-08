---
name: general-coding
description: 通用编码技能,审查时必读,初次编码结束准备整理刚才的代码时必读
---

# 通用编码约定

局部变量、循环变量与模式匹配变量禁止单字母或模糊缩写，须能直接看出含义
[rules/naming-full-identifiers.md](rules/naming-full-identifiers.md)

方法命名与参数语义须一一对应，不要让调用方同时承担多种职责或引入可合并的歧义参数
[rules/api-single-semantics.md](rules/api-single-semantics.md)

单函数内只调用一次的逻辑默认内联，同函数多次调用用局部闭包，类级方法仅用于跨函数复用、可测性或明显可读性提升
[rules/local-encapsulation.md](rules/local-encapsulation.md)

# 维护此文档

在通用编码约定部分增加一句话描述和文档链接，然后在 `rules` 文件夹里新增对应的详细描述
