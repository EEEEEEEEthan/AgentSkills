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

杜绝非必要防御代码；不在消费处叠冗余判空/长度兜底，风险在入口或边界集中处理
[rules/no-unnecessary-guarding.md](rules/no-unnecessary-guarding.md)

简洁优先于最小 diff；无额外封装理由时直接字段优于绕弯封装；对既有写法保持核对，收工时选最直、责任最清晰的一版
[rules/clarity-over-minimal-diff.md](rules/clarity-over-minimal-diff.md)

写代码要慎重：先理清顺序与分支再动手，避免多处补丁式特殊判断彼此打架
[rules/deliberate-coding.md](rules/deliberate-coding.md)

注意内存安全：回调/订阅成对解除、弱引用与释放顺序、循环引用与延迟销毁上要有明确所有权
[rules/memory-safety.md](rules/memory-safety.md)

在稳定边界预留窄扩展点，避免为未发生需求堆抽象
[rules/extensibility.md](rules/extensibility.md)

# 维护此文档

在通用编码约定部分增加一句话描述和文档链接，然后在 `rules` 文件夹里新增对应的详细描述
