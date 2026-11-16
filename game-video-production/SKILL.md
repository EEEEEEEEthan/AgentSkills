---
name: game-video-production
description: 用游戏资产和实机画面拍视频时使用：资产展示、玩法演示、宣传片、预告、短剧、讲解片。覆盖剧本、配音、字幕与头像、分镜时间、逐帧录制、混音、编码与交付的整条流程。触发词：拍视频、做个视频、出个视频、宣传片、演示片、预告片、showreel、短剧、讲解。
---

# 用游戏资产拍视频

一条可重跑的流水线：**剧本 → 配音（真实时长）→ 分镜时间 → 导演脚本 → 逐帧录制 → 混音 → 编码 → 抽帧验收**。

原则只有一条：**画面由 `show_shot(镜头 id, 进度 t)` 算出来**，不用 Tween、不用物理、不靠实时播放。同一进度永远得到同一帧，所以单帧预览、整片重录、只重拍一场都不会打架。

第 2、3、7 节（配音、字幕、编码验收）与引擎无关；第 0–6 节是 **Godot 4.8** 的现成实现，换引擎时只重写这几节。

## 0. 环境

```powershell
py -3 .engine.py --headless --path . --import     # 首次：下载引擎 + 导入资产
# 录制时直接用引擎可执行文件（.engine.py 只要看到 "ERROR:" 行就杀掉引擎，
# 而它的导入收尾会打印一行无害的 ERROR: Parameter "singleton" is null.）
& "$env:USERPROFILE\godots\4.8-beta3\Godot_v4.8-beta3_win64.exe" --path . ...
py -3 -m pip install --user websockets imageio-ffmpeg numpy pillow   # 配音 + 编码 + 音频/图像处理
```

- 配音统一用**豆包语音合成 2.0**（双向流式 WebSocket，`seed-tts-2.0`），把豆包官方 demo 里的 `protocols.py` 复制到 `.export/<slug>/tts/`；密钥从环境变量 `DOUBAO_API_KEY` 读，**不要写进脚本或提交**。
- 系统通常没有 ffmpeg，一律用 `imageio_ffmpeg.get_ffmpeg_exe()` 拿可执行文件。

## 1. 落点

| 放哪 | 放什么 |
| --- | --- |
| `app/<片名>/` | `film.tscn` + 同名薄 `.gd` + 只被它引用的 `.glb`/字体/头像。跟随仓库"按功能分目录"的约定 |
| `.export/<slug>/` | 全部中间产物（已 gitignore）：`narration.json`、`timeline.json`、`capture.gd/.tscn`、`frames/`、`audio/`、`avatars/`、`*.mp4` |
| 用户确认成片后 | 只清理 `frames/` 与 `*.mp4`；`narration.json`、`timeline.json`、逐句音频、脚本留着，它们是重录的唯一依据 |

## 2. 配音：先有声音，再有画面

`narration.json`：每个镜头一条。字段：

- `id` 镜头 id；`who` 说话人（与头像文件名对应）；`tag` 头衔/身份；`narration` 台词全文；`caption` 字幕（**通常就等于台词全文**）；`gap` 可选，句尾留白；纯画面卡用 `seconds`。

```powershell
$env:DOUBAO_API_KEY = "..."                      # 只放在当前 shell
py -3 .export/<slug>/make_narration.py           # 逐句合成 → audio/tmp/<id>.mp3 → audio/narration/<id>.wav
py -3 .export/<slug>/make_bgm.py                 # 没有现成 BGM 时合成一段循环
py -3 .export/<slug>/build.py all                # 真实时长 → timeline.json → 混音 audio/master.wav
```

**硬规则：**

1. **绝不拉伸/压缩语音。** 不用 `atempo`、不用改 `speech_rate` 去凑时长。时长不合适就改分镜时间（`seconds`/`gap`）或删改台词，让画面服从声音。
2. **只重做改动过的句子。** 逐句保存 mp3/wav，按台词文本哈希判断是否已存在；合格音频直接复用。改一版只重新合成被改动的那几句。
3. **一个角色一个音色，且音色要能听出区别。** 选角后抽两段估算基频（中位 F0）：同性别角色至少差 15–25 Hz，或换成不同音区/年龄感；两个低沉男声放在一起，观众会分不清。
4. 双向流接口对部分音色不开放，先逐句试；失败重试 2–3 次并换可用音色。
5. 每句合成后解码成 22.05 kHz 单声道 WAV，脚本打印时长；有静音/空文件立即重试。
6. 中文按 5–6 字/秒估时长；先跑一遍看总长，再决定删字还是加镜头。

## 3. 对白节拍：留白要有，但不能拖

- **对白之间**：连续台词的行间停顿控制在 **0.5–0.8 秒**。`gap` 默认给 0.2–0.3，再叠一个全局 `EXTRA_GAP`（0.4–0.5）即可；不要每条都留 1.5 秒以上。
- **真正需要呼吸的地方**：幕间、场景转换、情绪重击，可以留 2–4 秒，让 BGM 和画面自己说话。
- **开场不要放长时间无台词画面。** 片头卡可以带旁白；纯画面开场不超过 3–5 秒，否则观众会觉得"卡住了"。
- 想强调一个地点/设定，用**字幕副标题**或一句旁白带过，不要单独插 8–10 秒静默大字卡。

## 4. 字幕与头像

**每一句台词都要有字幕。** 静场/纯画面镜头不显示字幕条。

版式（底部横条）：

```
┌────────────────────────────────────────────┐
│ ┌──────┐  头衔 · 人名（白色）              │
│ │ 头像 │                                    │
│ └──────┘  台词全文（白色，左对齐，≥2 行）   │
└────────────────────────────────────────────┘
```

实现要点：

- 字幕条背景 **必须画在头像/名字/文字之下**。Godot 里给 `ColorRect` 设 `z_index = -1`，或把背景节点放在最前面；否则半透明条会把头像压暗一层，黑白后处理直接糊掉。
- 头像用 `TextureRect`（左）+ 名字 `Label`（右上，纯白 + 黑描边）+ 台词 `Label`（右下，纯白 + 黑描边，`autowrap`）。
- 头像与名字只在有台词时显示；`set_caption("")` 同时隐藏整条字幕。
- 字幕文本用**台词全文**，不要只放摘要；摘要另作标题卡用。
- 名字格式统一为 **「头衔 · 人名」**（如「记录法官 · 威尔弗雷德」），不要名在前。

### 头像怎么来

- 单独渲染 256×256 的**头肩特写**：相机放角色正前方约 0.9–1.1 m，看向头部，fov 35–40；**浅灰背景 + 强主光**，不要用深色背景。
- 为什么强调对比度：成片常会转黑白/降饱和，深色背景 + 深色西装会糊成一团。浅底、亮脸、深衣服才有轮廓。
- 新生成的 PNG 不经过 Godot 导入管线时，直接 `Image.load_from_file(ProjectSettings.globalize_path(path))` + `ImageTexture.create_from_image()` 加载，别依赖 `load()`。
- 旁白没有实体角色时，做一张统一标识（如白底黑问号）即可。

## 5. 场景：一个导演脚本

`film.gd` 只有几个入口，其余都是私有小函数：

```gdscript
func show_shot(shot_id: String, t: float) -> void:   # t ∈ [0,1]，整场由它算出来
	reset_stage()
	match shot_id: ...
func reset_stage() -> void:                          # 舞台、可见性、字幕卡全部复位
	%Santa.position = SANTA_POS
	%Marker.hide(); %Title.hide()                     # 否则上一场的标题/红圈会漏到下一场
func set_caption(text: String, index: int, total: int) -> void:
func set_tag(text: String) -> void:                  # 头衔 · 人名
func set_speaker(who: String) -> void:               # 切换头像
```

- 相机统一 `_aim(pos, target, fov)`：位置、`look_at`、fov 三个都插值，别写死。
- 角色动画：`%Santa.find_child("AnimationPlayer", true, false)` → `play("Idle")` + `seek(fmod(秒, 长度), true)`，逐帧都 seek，动画才是确定的。
- 道具、载具用模型自带的可动部件按名字 `find_child`；不要改资产文件。
- 常驻 UI（水印、`03 / 09`、字幕条）放在一个 `CanvasLayer` 里，位置用锚点，**不要**固定像素。
- 字体：CJK 必须自带（Godot 默认字体没有汉字）。把 `NotoSansSC-Bold.otf` 放同目录，Theme 的 `default_font` 指过去：

```powershell
Invoke-WebRequest -Uri "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Bold.otf" -OutFile "app/<片名>/NotoSansSC-Bold.otf" -UseBasicParsing
```

## 6. 手写 `.tscn` 的坑

1. **UTF-8 无 BOM**。PowerShell 的 `Set-Content -Encoding utf8` 会加 BOM，引擎报 `Parse Error: Expected '['`。用 `[System.IO.File]::WriteAllText($p, $c, (New-Object System.Text.UTF8Encoding($false)))`。
2. `[sub_resource]` 必须写在**引用它的节点之前**，否则 `Condition "!int_resources.has(id)" is true`。
3. 脚本里用 `%Node` 的节点，tscn 里必须有 `unique_name_in_owner = true`。
4. 给 GLB 实例设 `global_transform` 会**连 scale 一起覆盖**。要缩放就乘进 Basis。
5. 节点顺序就是绘制顺序；需要"背景在下、内容在上"时宁可用 `z_index` 明确写出来，不要靠插入位置猜。

## 7. 逐帧录制

`capture.tscn` + `capture.gd`（见 `templates/`）：

```powershell
# 单帧预览：摆机位、查构图、查字幕条，比重录整片快一百倍
& $godot --path . --disable-vsync res://.export/<slug>/capture.tscn -- `
    --timeline=res://.export/<slug>/timeline.json --film=res://app/<片名>/film.tscn --still=drive:0.8
# 整片
& $godot --path . --disable-vsync --fixed-fps 30 res://.export/<slug>/capture.tscn -- `
    --timeline=... --film=...
```

- `--fixed-fps 30` 让每帧 delta 恒为 1/30；每帧 `await process_frame` → `await RenderingServer.frame_post_draw` → `save_jpg`。
- **时间线一变就要整片重录**：帧号与音频偏移全都变了，不能只补拍几段。
- 长片可以拆成几个进程并行录制，但那只为了速度；**产出始终是一条完整视频**（见第 9 节）。

## 8. 画面调校（夜景/悬疑模板）

- `Environment`：ambient 0.3、`tonemap_mode = 2`、`glow_intensity 0.55`、`fog_density 0.009`。
- 灯：冷色 `DirectionalLight3D`（月光，energy 1.0，开阴影）+ 暖色路灯 `OmniLight3D`（energy 3，range 9）+ 车灯 `SpotLight3D`（energy 20+）。
- 地面：资产自带地形常有一块突兀色块，铺一张 `PlaneMesh` + 同色材质盖住（y=0.015）。
- 雪/雨：`GPUParticles3D`，`emission_box_extents` 覆盖镜头区，`preprocess` 给几秒让开场就有粒子。
- 黑白/低饱和成片：在编码阶段用 `hue=s=0` 等滤镜统一处理；所有 UI（头像、字幕）也要按"最终是黑白"来检查对比度。

## 9. 编码与验收

**只交付一条完整视频，不要把成片切成几段。** 需要并行时可以生成临时分段，最后用 `concat -c copy` 合成一条，再删掉临时段。

```powershell
$ff = py -3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"
& $ff -y -framerate 30 -i ".export/<slug>/frames/%06d.jpg" -i ".export/<slug>/audio/master.wav" `
  -c:v libx264 -preset slow -crf 22 -vf "scale=out_range=tv,format=yuv420p" `
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv `
  -c:a aac -b:a 128k -ac 1 -shortest -movflags +faststart ".export/<slug>/<slug>-v1.mp4"
```

- **必须写 `out_range=tv`**，否则得到 `yuvj420p` 全范围，部分播放器发灰。
- 音频用 `loudnorm=I=-15:TP=-1.5`（或混音阶段归一化）；目标 `mean_volume` 高于 -20 dB，别让用户觉得小声。
- 验收：
  - `ffmpeg -i` 核对时长/编码/体积；
  - `volumedetect` 看 mean/max，`astats` 看 `Flat factor`（0 表示没有削波）；
  - 抽 8–12 帧**真的看图**：字幕有没有截断、头像是否清楚、主角是否出画、镜头是否对着空地；
  - 确认台词与字幕一一对应，没有"有声无字幕"的句子。
- 文件名带版本号 `-v1/-v2`，旧版本别覆盖；附件上限 20MB，超了调高 CRF，不降分辨率。

## 10. 交付

成片用**一个** `multica issue comment add --attachment` 附件贴到 issue 评论里，说清"这版改了什么"（改了哪几句、哪几个镜头、时长变化）。中间产物在用户确认前一概不删。

## 模板

| 文件 | 作用 |
| --- | --- |
| `templates/capture.gd` / `capture.tscn` | 逐帧录制器：读 timeline.json，逐镜头 `show_shot` + `set_speaker`/`set_tag`/`set_caption`；支持 `--still=镜头:进度` |
| `templates/film_skeleton.gd` | 导演脚本骨架：reset_stage / show_shot / _aim / 字幕与头像 |
| `templates/film_skeleton.tscn` | 场景骨架：夜景环境、月光、相机、CanvasLayer 字幕层、雪粒子 |
| `templates/portrait.gd` | 渲染 256×256 头肩头像：浅灰底、强主光、正面机位 |
| `templates/make_narration.py` | 豆包 2.0 双向流逐句合成 → wav；按文本缓存，只重做改动句 |
| `templates/make_bgm.py` | 合成一段循环 BGM（拨弦 + 铃铛），无版权风险 |
| `templates/build.py` | 真实语音时长 → `timeline.json`（含 who/tag/字幕）+ `audio/master.wav` |
| `templates/narration.example.json` | 镜头清单样例（含说话人/头衔） |

资产从哪来、怎么免账号下载、真实比例和可动部件怎么查：`references/polyfork.md`。
