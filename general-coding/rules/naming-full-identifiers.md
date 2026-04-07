# 约定：局部与循环变量命名必须完整

## 规则

- **禁止**在局部变量、循环变量、模式匹配变量中使用单字母或模糊缩写。
- 命名须能直接看出含义，例如：当前节点用 `node`/`control`，子节点用 `child`，若需类型区分用 `childControl`、`childNode`；容器用 `container`，不要用 `n`、`cc`、`cont`、`p` 等。

## 不符合

```csharp
var n = stack.Pop();
if (child is Control cc) processStack.Push(cc);
```

## 符合

```csharp
var node = stack.Pop();
if (child is Control childControl) processStack.Push(childControl);
```
