---
name: godot-engine
description: Godot 引擎使用与行为规范。用于处理引擎对象生命周期、布局刷新、尺寸读取、InstancePlaceholder、CallDeferred、process_frame、Engine.IsEditorHint 与 C# 调用成本相关问题时。
---

# Godot 引擎使用

## 使用方式

先读本文件，只拿总规则。

当任务落到具体问题时，再按需读取对应文档：

- `InstancePlaceholder`、依赖注入、`_ready()` 时机：见 [instance-placeholder.md](instance-placeholder.md)
- 容器布局、尺寸读取、同帧刷新：见 [layout-refresh.md](layout-refresh.md)
- `Engine.IsEditorHint()`、引擎属性访问、C# 调用成本：见 [csharp-api-cost.md](csharp-api-cost.md)

## 总规则

1. 涉及时序时，先确认节点是否已经进树，再决定是否能访问依赖或尺寸。
2. 需要“本帧得到结果”时，优先显式触发布局或更新，不要默认拖到下一帧。
3. 在 C# 中把引擎 API 当成高成本边界，避免重复读写。
4. 默认优先稳定、可维护的路径与生命周期方案，避免依赖脆弱时机。

## 快速分流

### 场景一：placeholder 替身节点要先注入依赖

不要急着 `create_instance()`，先看 [instance-placeholder.md](instance-placeholder.md)。

### 场景二：这帧就要读到正确尺寸或位置

不要先 `CallDeferred` 或 `await process_frame`，先看 [layout-refresh.md](layout-refresh.md)。

### 场景三：C# 逻辑里频繁访问引擎对象

先检查是否能缓存、合并写回或减少跨边界调用，具体见 [csharp-api-cost.md](csharp-api-cost.md)。
