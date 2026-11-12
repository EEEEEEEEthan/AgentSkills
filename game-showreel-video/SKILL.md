---
name: game-showreel-video
description: 用游戏资产和实机画面拍视频（资产展示、功能演示、宣传/预告、玩法讲解、成果回顾）时使用，产出带中文旁白、烧进画面的字幕和 BGM 的 MP4。触发词：拍视频、做个视频、出个视频、宣传片、演示片、预告片、资产展示、showreel、成果回顾。
---

# 游戏资产视频

把游戏里的资产或跑着的游戏画面做成一段能直接播给人看的视频：画面全部来自实机/资产预览，字幕烧进画面，旁白用神经语音合成，BGM 压低垫底。

这个技能**不只用来总结工作**：同一套流程可以拍单体资产展示、功能/玩法演示、宣传预告、玩法讲解，以及工作成果回顾。

## 与具体项目解耦

这个技能面向**任意用 Godot 做的游戏项目**，不绑定某个仓库。下文用 `<WORK_DIR>` 表示「项目里已被 gitignore 的产物子目录」（如 `.export/<slug>/`、`build/showreel/`），用 `<PROJECT>` 表示任意项目。文中的 `.export/<slug>/`、`main.tscn`、`tests/`、以及模板里的类名（`TestScriptBase`、`IsometricCamera`、`GameSession` 等）都只是示例，落地时按目标项目的目录、节点名与引擎封装替换。

## 何时执行

用户要一段**看得见游戏资产或实机画面**的成片时用。只要截图、PPT、文字周报时不用这个技能。

## 先定视频类型（决定分镜怎么写）

| 类型 | 画面来源 | 分镜重点 |
| --- | --- | --- |
| 资产展示 / 建模验收 | 资产预览场景或主场景里的单体建筑、道具、角色 | 环绕/转台/推近，材质、细节、比例、昼夜与光照 |
| 功能 / 玩法演示 | 真实主场景，真实操作或状态推进 | 触发前后对比，读数、UI、动画要看得清 |
| 宣传 / 预告 | 真实画面剪辑 | 节奏与转场优先，短镜头、强画面 |
| 玩法讲解 / 教程 | 真实画面 + 步骤字幕 | 一步一镜，字幕说清在做什么 |
| 工作成果回顾 | 按提交/需求分章，无画面成果用滚动文本补 | 覆盖需求编号，说清这版改了什么 |

类型决定镜头怎么写、要不要旁白、字幕点名什么，开工前先和用户对齐。

## 开工前必须问清的五件事

缺一条就用 `ask_user` 问，不要自己拍板：

1. **用途与主题**：给谁看、要传达什么、属于上面哪种类型。
2. **素材范围**：用哪些资产/场景/功能；是否要求画面全部来自实机。
3. **总时长与分组**：全长目标（默认 2 分钟左右，110–140 秒）；按板块/资产分章、每章 14–26 秒；片头片尾卡各 5–6 秒。
4. **声音**：合成旁白 + BGM（默认）、只要字幕、还是只要 BGM。
5. **交付去向**：只贴聊天（默认）还是同时发群/另存目录。

## 产物落点（硬规矩）

- 所有脚本与中间产物放在**项目里已被 gitignore 的目录**（`<WORK_DIR>`）下新建的一个子目录里，例如 `.export/<slug>/`、`build/showreel/`。仓库里没有可用目录就先补一条 gitignore 再建；绝不放仓库根、`tests/`、`tools/` 这类会被跟踪的位置。
- 目录结构：`narration.json`（唯一内容源）、`timeline.json`（帧预算）、`capture_base.gd` + 每章一个 `ch*.gd`、`make_narration.py`、`build.py`、`check_*.py`、`text/`（章节要滚动的真实文本）、`frames/`（逐帧 JPG）、`audio/`（旁白与 BGM）、`out.mp4`。
- **中间产物在用户确认视频做好之前一个都不删**：`frames/` 常有 1–2GB，`audio/` 有几十个 wav，脚本更是重录的唯一依据。用户说过「不要清理」就全程留着；只有在用户明确确认成片没问题之后才清理，并保留脚本与 `timeline.json`。

## 不跑游戏测试（硬规矩）

**拍视频不需要跑游戏的测试。** 成片的依据是画面与声音本身：录制脚本 + 抽帧看图 + 字幕覆盖检查 + 音频响度就够了。

- 不要为了片子里一句「测试全绿」去跑 `--all` 之类的全量测试（几分钟起步，还容易撞上限判红），更不要让它阻塞出片。
- 章节需要演示「质量类」成果时，用**已有的真实材料**（仓库里的测试日志、`git show` 的 diff、提交记录）做滚动文本，并在字幕里说清是什么；没跑就说没跑，不要写成跑过且全绿。
- 只有用户明确说「先跑测试」时才跑，结果如实进字幕。

## 画面必须来自真实资产/实机

- 每一帧都从跑着的场景里抓：`await get_tree().process_frame` → `await RenderingServer.frame_post_draw` → `get_viewport().get_texture().get_image().save_jpg(path, 0.92)`。
- 资产展示用项目里的真实模型与材质，可以在预览场景里自建转台/相机轨道；**不要用外部渲染图、截图拼贴或占位模型**冒充实机。
- 功能演示走真实主场景与真实状态推进，不要为了画面好看伪造读数。
- 引擎参数 `--fixed-fps 30 --disable-vsync`：帧号与时间轴严格对齐，编码时直接按 `%06d.jpg` 顺序吃。
- 场景摆设优先复用项目里现成的预览脚本与测试夹具，把它们的摆法抄进自己的 `ch*.gd`；**不要修改这些既有文件**，也不要在游戏里加播放/字幕/调试开关。
- 镜头动作写成 `update(t: float)` 回调（`t` 是镜头进度 0–1），相机位置、参数、UI 状态都在这里变；先把 `edge_scroll_enabled` / `world_input_enabled` 关掉，免得输入跟脚本抢镜头。
- 提交记录、diff、测试日志这类没有画面的内容，可以单独做一章滚动文本；但它是补充章，不替代实机画面。

## 旁白：神经语音，不要 SAPI

- 首推 `edge-tts` 的 `zh-CN-XiaoxiaoNeural`（微软神经语音，Warm 音色，最自然）。同等自然度的替代：`zh-CN-YunxiNeural`（活泼）、`zh-CN-YunyangNeural`（新闻播音）、`zh-CN-YunjianNeural`（有力度）。
- **不要用 Windows SAPI**（`Microsoft Huihui Desktop` 之类）：机械感强，用户一定会要求换掉。
- 装与试音：

```bash
python3 -m pip install --user edge-tts
python3 -m edge_tts --voice zh-CN-XiaoxiaoNeural --rate "+0%" --text "先合成一句确认网络通" --write-media /tmp/voice_test.mp3
```

> Windows 上 `python3` 换成 `py -3`。

- edge-tts 需要联网，网络不通会直接抛错；先在一条上试通，再批量（`templates/make_narration.py` 会逐句出 mp3 并用 ffmpeg 转 22.05kHz 单声道 wav）。
- **时长由旁白反推，不要先定帧数**：先出 wav → `wave` 量长度 → `frames = round((voice_seconds + gap) * fps)`（`gap` 0.4–0.8 秒）→ 写 `timeline.json`。总时长超上限就先压 `gap`，再逐条删字（编号要保留）。

## 字幕与文字

- 字幕直接画进画面：`CanvasLayer(layer=100)` + 底部 `Label` + 半透明底条（alpha 0.8 以上，亮场景才压得住），另有左上章节标题与右上「第几章/共几章」。
- 字体按**项目规范**选（项目若有 AGENTS.md / UI 规范就照它）；画面文字优先用游戏内字体，缺字或小字号不适合时再回退系统字体（Windows：`Microsoft YaHei UI → Microsoft YaHei → SimHei`）。不要在这个技能里写死某个字体文件；底条上文字一律加阴影与描边，保证任何底色都能读。
- 出图前先量宽度：`templates/check_text_width.gd` 用同一个字体对象量每条字幕的像素宽度，可用宽度 = 画面宽 − 左右内边距，超宽就缩字号或拆行，别等看完片子才发现被截断。
- 每条镜头至少点名一个要点：成果回顾点需求编号（`#258`），资产展示点资产名/参数，功能演示点功能点。成果回顾可配 `check_coverage.py` 做编号覆盖检查。

## 编码与体积（要能贴进聊天）

- 系统通常没有 ffmpeg：`py -3 -m pip install --user imageio-ffmpeg`，再用 `py -3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"` 取路径。新版 ffmpeg 没有 `-vsync`（改用 `-fps_mode passthrough`），也没有 `ffprobe`（用 `ffmpeg -i` 看规格）。
- 目标：1280×720 / 30fps / H.264 yuv420p + AAC 单声道（项目另有分辨率规定时按项目），`-movflags +faststart`。
- 先 `-preset slow -crf 23` 试编一次量体积，再按 20MB 上限**只往上抬 CRF**（经验值：满屏 dither 的游戏画面、2 分钟、720p，要 CRF 30–31 才落进 17–20MB），**不要降分辨率**。
- 混音母带：旁白按镜头起始帧铺到位，BGM 在旁白段增益 0.10、无旁白段 0.22、最后 2 秒淡出，整体峰值归一到 −1 dBFS；`volumedetect` 的 `mean_volume` 应当高于 −20dB 才算够响（低于 −25dB 用户会觉得小声）。

## 交付与版本号

- 每次出片都用 `send_attachment` 贴到聊天里（工具上限 20MB），并说清「这版改了什么」。
- **文件名带版本号**：`<slug>-v1.mp4`、`<slug>-v2.mp4`、`<slug>-v3.mp4`……每次改动都是新文件名，避免客户端/播放器按同名缓存拿到旧片。旧版本留在磁盘上不要覆盖。
- 同时留一份到项目约定的产物目录（例如 CI/Hub 注入的 artifacts 目录；没有就用 `<WORK_DIR>` 同级的上传目录），文件名同样带版本号。

## 流程（按顺序做）

1. **定类型与分镜**：先按上面的类型表定路线，再写 `narration.json`（每章 `title`/`issues`/`shots[]`，每个镜头 `id`/`caption`/`narration`/`gap`；纯文字卡用 `seconds` 代替旁白）。
   - 资产展示：列要拍的资产、角度与材质/细节重点。
   - 功能演示：列要触发的状态、操作与要看清的读数。
   - 成果回顾：`git log --since="<起点>" --pretty=%s` 数提交、抽需求编号、挑出能看见的成果。
2. **环境**：新 worktree 或干净目录先用项目「打印引擎路径」的办法拿到引擎可执行文件，跑一次 `"$GODOT_BIN" --path . --headless --import`（没有 `.godot/` 时模型与字体导入产物缺失）；装 edge-tts 与 imageio-ffmpeg。
3. **旁白与帧预算**：`make_narration.py` → `build.py timeline`，核对总时长在目标区间、每章 14–26 秒、片头片尾卡 5–6 秒。
4. **逐章录制**：一章一个独立进程，失败只重录那一章（帧号全局连续，重录会覆盖同一段）：

```bash
"$GODOT_BIN" --path . --disable-vsync --fixed-fps 30 -- \
  --test=res://.export/<slug>/chX.gd \
  --showreel-timeline="$PWD/.export/<slug>/timeline.json"
```

每章要打印 `SHOWREEL_BEGIN <章 id> <首帧> <帧数>` 与 `SHOWREEL_END <章 id> <末帧>`，脚本自己 `_expect` 帧号对不对；对不上就停在这一章修。
5. **混音**：`build.py audio` 出 `audio/master.wav`。
6. **编码 + 验收**：编码后必查时长/编码/字节数/`volumedetect`；所有类型都跑 `check_frames.py`（每个镜头中位帧 ≥30KB、无连续 5 帧 <12KB），成果回顾再跑 `check_coverage.py`（需求编号全覆盖）；抽 8–12 帧**真的用 read 看图**确认字幕与画面对得上。
7. **贴聊天**（文件名带版本号）+ 说明改动点。
8. 用户确认后才清理中间产物；没确认就留着。

## 模板（`templates/`）

复制到 `<WORK_DIR>` 后按目标项目改路径与节点名即可（模板里的类名/资源路径都来自示例项目）：

| 文件 | 作用 |
| --- | --- |
| `capture_base.gd` | 录制基座：窗口尺寸、字幕层、逐帧落盘、镜头帧号对账、相机平移/换档助手 |
| `example_chapter_standalone.gd` | 自建夹具/资产预览场景的章节示例（正交相机轨道 + 参数动画，不依赖主场景） |
| `example_chapter_main_scene.gd` | 在真实主场景里搭镜头的章节示例（示例内容取自一个城市建造游戏，按自己项目的场景改写） |
| `make_narration.py` | edge-tts 批量合成 → 转 wav，打印每条时长与总时长 |
| `build.py` | `narration.json` → `timeline.json` → 混音母带 `audio/master.wav` |
| `check_coverage.py` | 需求编号覆盖检查（成果回顾用；从 `git log` 抽 `#\d+`，逐个在字幕/旁白里找） |
| `check_frames.py` | 纯色/停帧检查（按镜头统计每帧 JPEG 字节数） |
| `check_text_width.gd` | 字幕宽度体检（超宽就打印 WIDE） |
| `narration.example.json` | 章节/镜头/字幕/旁白的真实样例（内容是「成果回顾」，其他类型照同样结构替换） |

章节脚本用**字符串路径**继承基座，别依赖 `class_name` 注册：`extends "res://<WORK_DIR>/capture_base.gd"`。

> 模板里的 `TestScriptBase`、`IsometricCamera`、`TileGrid`、`GameSession`、`TerrainView`、`main.tscn`、`tests/_*_preview.gd` 都是示例项目的类型与路径，复制后要换成目标项目对应的封装。

## 踩过的坑

- `--test=` 必须放在 `--` 之后才会成为用户参数：`godot --path . --fixed-fps 30 -- --test=res://...`。放错位置引擎会正常启动主场景然后一直挂着（看起来像卡死）。
- 点开头的目录（`.export/`）里的脚本能被 `load()`，但 `class_name` 不一定注册到全局，所以章节脚本用 `extends "res://...gd"`。
- 没有音频设备时 `WASAPI: init_output_device error` 会刷屏，不影响录帧，忽略即可。
- 项目开了 `window/stretch/*` 时字幕用锚点定位，不要写死像素坐标。
- 逐帧落盘 40–80ms/帧，3000 帧约 4 分钟；所以一章一个进程，出错只重录一章。
- 抽帧看图不能只看文件大小：字幕截断、取景把主角拍出画面、镜头对着空草地，都只有真看图才发现。
