---
name: godot-sharp
description: Godot C# 脚本与引擎功能交互时的编写规范
---

# Godot C# 脚本规范

## 占位符（InstancePlaceholder）

1. **必须先理解再动手**：勾选「**加载为占位符**」或在 tscn 中写 `instance_placeholder=` 时，**运行时**该子项是 **`InstancePlaceholder`**（继承 `Node`），不是子场景根节点的类型。实例化应使用 **`CreateInstance()`**，不能把占位节点当成 `PackedScene` 路径去 `GD.Load`，也不能对占位节点做 `Duplicate()` 当作「从模板克隆」。
2. **能用占位就不要用路径**：若场景已用占位符表达「延迟加载的子场景」，C# 侧应通过 **`GetNode<InstancePlaceholder>("%...")` + `CreateInstance()`**（配合唯一名与 `field ??=`）生成实例；**不要**再写死 `res://...` 的 `PackedScene` 路径作为平行方案，除非没有占位节点可用。

## 内嵌脚本（builtin）与节点类型一致

子场景或节点上 **内嵌 GDScript** 若写 **`extends SomeType`**，挂载该脚本的 **根节点 `type=` 必须与 `SomeType` 一致**（例如 `extends Button` 则根节点须为 `Button`）。只改脚本 `extends` 而不改 tscn 节点类型会导致编辑器与运行时行为不一致。

## tscn 脚本访问场景内部节点

脚本挂载在 tscn 上时，访问场景内部的子节点应使用 **unique_name + field 缓存**，而非 Export。

### Export 的边界

**不要**对「仅由本场景结构决定、不会在 Inspector 里改指向」的内部引用做 `[Export]`（例如占位节点路径、固定子节点）。**只有**在设计上明确允许策划/美术**在编辑器中改绑定**时，才用 Export。

### 1. 在 tscn 中为节点设置 unique_name

在场景编辑器中选中节点，勾选 **Unique Name in Owner**，或在 tscn 文本中添加：

```
unique_name_in_owner = true
```

### 2. 在 C# 中用 GetNode + field 缓存

使用 `GetNode("%NodeName")` 通过 unique name 获取，并用 `field ??=` 做懒加载缓存：

```csharp
using System.Diagnostics.CodeAnalysis;

[field: MaybeNull] TextureButton BtnWishlist => field ??= GetNode<TextureButton>("%ButtonWishlist");
[field: MaybeNull] Label LbTitle => field ??= GetNode<Label>("%LabelTitle");
```

### 3. 可选节点用 GetNodeOrNull

若节点可能不存在（如条件显示的 UI）：

```csharp
[field: MaybeNull] Control HighlightCursor => field ??= GetNodeOrNull<Control>("%HighlightCursor");
```

### 4. 不推荐

- ❌ `[Export] Button btnXxx` + 在编辑器中拖拽 NodePath
- ❌ 每次访问都 `GetNode("%Xxx")`（无缓存）
