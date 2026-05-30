# 垂直同步与子窗口渲染拉回

## 问题

独立子窗口（`embed_subwindows=false`）上，相机或视口内容在逻辑位置已更新后，画面却短暂回到旧位置，像被「拉回」一帧。常见特征：

- 关闭位置平滑后仍会出现，容易误判为拖拽或相机脚本问题。
- 累计平移一段距离后更明显；刚开始几乎看不出。
- 多出现在透明、无边框、置顶 overlay 类子窗口（如桌面条带游戏窗）。

根因通常是 **交换链呈现** 与 **逻辑更新** 不同步，而非 `Camera2D` 未 clear。2D 相机没有独立的 clear 设置；清屏由 `Window` / `Viewport` 的 `transparent_bg` 与项目透明背景选项负责。

## 典型诱因

- 项目设置 `display/window/vsync/vsync_mode = 0`（`VSYNC_DISABLED`）：无垂直同步时，子窗口可能在相机已移动后仍短暂呈现上一帧缓冲，位移越大「拉回」越显眼。
- 子窗口 `transparent = true` + Windows DWM 合成：透明窗对缓冲时序更敏感，无 VSync 时更易暴露。
- 相机在 `physics_frame` 更新、显示刷新率更高且无插值：会放大「旧帧被呈现」的观感（与 VSync 关闭叠加时更常见）。

## 排查

1. 确认 `Project Settings → Display → Window → VSync → VSync Mode`；若为 **Disabled**，优先改为 **Enabled** 或 **Mailbox** 复现对比。
2. 确认问题是否只出现在 **非嵌入子窗口**（`Window.new()` / 场景里独立 `Window` 节点），主窗口正常而游戏窗闪回。
3. 排除误判：用调试 overlay 同时显示 `Camera2D.position.x` 与 `get_screen_center_position().x`；若逻辑值连续变化而画面跳变，偏向呈现/合成而非脚本算错。

## 默认做法

- 面向玩家的 **独立 overlay 子窗口** 默认开启 VSync（`vsync_mode = 1`），或需要低延迟时用 **Mailbox**（`3`）。
- 保持 `transparent_bg` / 项目 `per_pixel_transparency/allowed` 配置完整；不要用「多清一次屏」代替 VSync。
- 若必须关 VSync，接受 overlay 在快速平移时可能出现 tearing / 旧帧闪现；相机侧 `force_update_scroll()` 无法从根本消除此类呈现问题。

## 运行时修改

```gdscript
DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED, game_window.get_window_id())
# 或
DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_MAILBOX, game_window.get_window_id())
```

## 相关设置

| 设置 | 说明 |
|------|------|
| `display/window/vsync/vsync_mode` | `0` 关闭，`1` 开启，`3` Mailbox |
| `display/window/subwindows/embed_subwindows` | `false` 时子窗口为独立 OS 窗口 |
| `Window.transparent` / `transparent_bg` | 透明合成路径，与 VSync 问题常同时出现 |

## 判断标准

子窗口平移/相机 pan 出现「闪回」，且关平滑、改拖拽逻辑无效时，**先查 VSync 与子窗口呈现**，再查相机脚本与 clamp。
