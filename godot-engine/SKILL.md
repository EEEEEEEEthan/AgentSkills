---
name: godot-engine
description: Godot 引擎使用与行为规范，在使用引擎对象、布局、尺寸、CallDeferred、process_frame、Engine.IsEditorHint 时使用
---

# Godot 引擎使用

## 布局刷新：同一帧内触发布局再读尺寸

需要在本帧内拿到正确的布局或尺寸时：

1. **先触发布局**：对相关 Container 调用 `FlushLayout()`（C# 扩展）或 `queue_sort()` / 依赖引擎的排序机制，使排序与 `UpdateMinimumSize()` 在本帧内完成。
2. **再读尺寸或执行逻辑**：在同一帧内调用 `GetCombinedMinimumSize()`、读取 `Size`/`Position` 或设置窗口位置等。

**不要**为“等布局算好”而延迟到下一帧：禁用 `CallDeferred(nameof(UpdateLayout))`、`await get_tree().process_frame` 等，再在下一帧读尺寸或执行逻辑。

**正确示例**（C#）：在 `UpdateWindowLayout()` 里先 `PanelContainer.FlushLayout()`，再 `PanelContainer.GetCombinedMinimumSize()`。

## C# API 成本：少用引擎 API

Godot 的 C# 绑定与引擎交互（P/Invoke）成本较高。应尽量减少对引擎属性的读写。

**Engine.IsEditorHint()** 是昂贵调用，每次都会跨越托管/原生边界。若多处使用，应封装并缓存（用 `??=` 或类似方式首次求值后复用）。

**适用场景**：每帧更新坐标、旋转等属性时，可做本地缓存，仅在值变化时写回引擎。

**做法**：用属性封装，内部维护 `Vector3?` 等缓存字段；setter 内先 `if(cache == value) return`，再同时更新缓存和 `Node.Position`/`Camera.Rotation` 等。
