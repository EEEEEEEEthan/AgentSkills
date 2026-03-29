# 布局刷新与尺寸读取

## 问题

你需要在当前帧立刻拿到正确布局、最小尺寸、窗口位置或控件尺寸。

这时最常见的错误是：

- `CallDeferred(...)`
- `await get_tree().process_frame`
- 先拖到下一帧，再读尺寸

这会把问题变成“时序碰运气”，而不是“当前帧显式完成布局”。

## 默认做法

如果目标是本帧拿到正确结果，顺序应该是：

1. 先触发布局或排序
2. 再读取尺寸
3. 再执行依赖这些尺寸的逻辑

## 推荐思路

### C#

对相关容器先调用 `FlushLayout()`，再读 `GetCombinedMinimumSize()`、`Size`、`Position` 等值。

### GDScript

优先使用 `queue_sort()` 或依赖容器本身的排序机制，再在同一轮逻辑里读取结果。

## 例子

```csharp
PanelContainer.FlushLayout();
Vector2 layoutSize = PanelContainer.GetCombinedMinimumSize();
```

重点不是具体 API 名字，而是顺序：

- 先让布局完成
- 再消费布局结果

## 不要这样做

下面这些通常是在掩盖时序问题：

- `CallDeferred(nameof(UpdateLayout))`
- `await get_tree().process_frame`
- “多等一帧试试”

如果只是为了拿正确尺寸，这些做法通常都不是首选。

## 适用场景

- 根据内容动态设置窗口大小
- 刷新列表后立刻定位或对齐控件
- 同帧内读取最小尺寸再决定布局
- UI 初始化时立即计算显示位置

## 判断标准

如果你在代码里看到“先延迟，再读取尺寸”，先停一下，优先改成“本帧显式刷新布局”。
