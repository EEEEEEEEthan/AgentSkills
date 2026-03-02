---
name: general-coding
description: 通用编码约定，如局部变量与循环变量必须完整命名、禁止单字母或缩写。在编写或审查 C#/GDScript 等代码时使用。
---

# 通用编码约定

## 命名必须完整

- **禁止**在局部变量、循环变量、模式匹配变量中使用单字母或模糊缩写。
- 命名须能直接看出含义，例如：当前节点用 `node`/`control`，子节点用 `child`，若需类型区分用 `childControl`、`childNode`；容器用 `container`，不要用 `n`、`cc`、`cont`、`p` 等。

**不符合：**
```csharp
var n = stack.Pop();
if (child is Control cc) processStack.Push(cc);
```

**符合：**
```csharp
var node = stack.Pop();
if (child is Control childControl) processStack.Push(childControl);
```

## 接口语义必须单一

- 方法命名与参数语义必须一一对应，不要让调用方同时承担“状态来源”和“状态校验”两份职责。
- 如果同一操作可以由单一参数表达（例如位置索引），不要再引入额外参数制造歧义。
