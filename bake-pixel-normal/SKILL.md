---
name: bake-pixel-normal
description: 从像素 diffuse 贴图烘焙 2D 法线贴图，颜色仅使用 GIMP 调色板（如 normal.gpl）中的条目。用于用户要求烘焙/重烘焙法线贴图、扩大法线过渡范围、或处理山体/剪影类 CanvasTexture 资产时。
---

# 烘焙像素法线贴图

## 何时使用

- 用户修改了 diffuse 图，需要同步法线贴图
- 需要从剪影/alpha 轮廓生成 Godot 2D 光照用的法线
- 用户要求法线颜色限制在 GIMP 调色板（通常 `normal.gpl`）内
- 用户要求调整法线过渡宽度（更宽/更窄的坡面）

## 快速执行

脚本路径：`~/.agents/skills/bake-pixel-normal/scripts/bake_normal.py`

```bash
# 默认 4×4 法线球（少梯度）
python ~/.agents/skills/bake-pixel-normal/scripts/bake_normal.py <diffuse.png> -o <normal.png>

# 8×8 法线球（更细腻）
python ~/.agents/skills/bake-pixel-normal/scripts/bake_normal.py <diffuse.png> -o <normal.png> --lut 8

# 项目内自定义法线球
python ~/.agents/skills/bake-pixel-normal/scripts/bake_normal.py <diffuse.png> -o <normal.png> --sphere path/to/sphere.png
```

内置法线球（技能目录）：
- `--lut 4` → `normal_sphere_4.png`
- `--lut 8` → `normal_sphere.png`
- `--sphere` 指定路径时覆盖 `--lut`

依赖：`pillow`（`pip install pillow`）

## 算法

1. 对每个不透明像素，向上下左右探测到**图内**透明边的距离（`--max-dist` 为半径）；**出界视为无轮廓，不算透明**
2. 用法线指向最近透明边界：`tx = left-right`，`ty = down-up`（**朝上 ty 为正 → 高 G**）
3. 归一化 `(tx, ty, 1)` 得 `(nx, ny, nz)`，转 RGB：`(nx*0.5+0.5)*255` 等
4. 从 **法线球图**（`normal_sphere_4.png` / `normal_sphere.png`）**提取全部像素色**作为调色板，在 RGB 空间找**最近色**
   - **禁止**按球图坐标 `(col,row)` 采样像素
   - `|nx|`、`|ny|` 均低于 `--flat` 时用 `(128,128,255,255)`；透明像素用 `(128,128,255,0)`
5. 4×4 球色更少 → 梯度层级更少；8×8 球色更多 → 更细腻

## 参数调优

| 参数 | 默认 | 效果 |
|------|------|------|
| `--max-dist` | 16 | 越大，过渡带越宽、坡度越缓 |
| `--strength` | 2.5 | 坡度强度；过大易饱和到球表边缘格 |
| `--flat` | 0.25 | 低于此坡度视为朝相机平面 |
| `--lut` | `4` | 内置法线球：`4` 少梯度，`8` 细腻 |
| `--sphere` | （无） | 自定义法线球路径，覆盖 `--lut` |

用户说「减少梯度」→ `--lut 4` + 降低 `--strength`、提高 `--flat` / `--max-dist`。  
用户说「更细腻」→ `--lut 8`。  
用户说「更陡」→ 增大 `--strength`。

## Godot 接入要点

`CanvasTexture` 的 `diffuse_texture` / `normal_texture` **不要**嵌套 `AtlasTexture`，否则 2D 光照会丢 diffuse 发白。

正确做法：

```text
CanvasTexture → 整张贴图 + 整张贴图法线
Sprite2D.region_enabled = true
Sprite2D.region_rect = 裁切区域 Rect2
```

多行图集时，各行共用同一 `CanvasTexture`，靠 `region_rect` 区分。

## 工作流

```
任务进度：
- [ ] 确认 diffuse 已保存
- [ ] 选择 `--lut 4` 或 `--lut 8`（或 `--sphere` 自定义），运行 bake_normal.py
- [ ] 若场景 region_rect 与图集行高不一致，同步 .tscn
- [ ] Godot 重开或重新导入贴图验证光照
```
