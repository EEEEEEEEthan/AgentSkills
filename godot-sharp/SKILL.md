---
name: godot-sharp
description: >-
  Godot C# 脚本编写规范。当编写 Godot C# 脚本、在 tscn 场景中访问子节点、或使用 Export 与 GetNode 时使用。
---

# Godot C# 脚本规范

## tscn 脚本访问场景内部节点

脚本挂载在 tscn 上时，访问场景内部的子节点应使用 **unique_name + field 缓存**，而非 Export。

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
