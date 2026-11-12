extends Node
## 示例项目里这里继承的是 TestScriptBase（测试入口）；复制到目标项目后改成项目自己的测试/场景基类。
## 游戏资产视频的录制基座：窗口尺寸、字幕层、逐帧取图落盘、章节与镜头的帧号对账。
##
## 章节脚本覆写 `_ready()`，先 `await _start_chapter(&"ch1_terrain", true/false)` 摆好世界，
## 再对每个镜头调 `await _record_shot(&"镜头 id", "字幕")` 并在回调里做镜头动作。
## 帧号一律取自 `timeline.json`（`build.py` 生成）：所有章共用一条连续帧序列，
## 因此编码时直接按 `%06d.jpg` 顺序吃即可。

## 分帧图落盘目录：复制到自己的 `<WORK_DIR>` 后把这里改成那个目录。
const FRAMES_DIRECTORY := "res://.export/showreel/frames"
const TIMELINE_ARGUMENT_PREFIX := "--showreel-timeline="
const TITLE_FONT_SIZE := 40
const CAPTION_FONT_SIZE := 30
const PROGRESS_FONT_SIZE := 22
const BACKGROUND_COLOR := Color(0.06, 0.07, 0.08)

var chapter_id: StringName = &""
var chapter_title := ""
var issues: Array = []
var frames_directory := FRAMES_DIRECTORY

var _chapter: Dictionary = {}
var _timeline: Dictionary = {}
var _overlay_root: Control
var _subtitle_font_resource: Font
var _chapter_ordinal := 0
var _chapter_count := 0
var _frame_index := 0
var _title_label: Label
var _caption_label: Label
var _progress_label: Label


## 读 timeline、摆好窗口与字幕层；[param with_background] 为真时铺一层深色底（片头片尾卡）。
## 返回章节字典，调用点一般只看帧数。
func _start_chapter(desired_chapter_id: StringName, with_background: bool) -> Dictionary:
	chapter_id = desired_chapter_id
	get_window().size = Vector2i(1280, 720)
	Engine.max_fps = 0
	get_tree().paused = false
	_timeline = _load_timeline()
	var chapters: Array = _timeline.get("chapters", [])
	_chapter_count = chapters.size()
	for index in chapters.size():
		var entry: Dictionary = chapters[index]
		if StringName(entry.get("id", "")) != chapter_id:
			continue
		_chapter = entry
		_chapter_ordinal = index + 1
	_expect(not _chapter.is_empty(), "timeline.json 里要有章节 %s" % chapter_id)
	if _chapter.is_empty():
		return {}
	chapter_title = String(_chapter.get("title", ""))
	issues = _chapter.get("issues", [])
	_frame_index = int(_chapter.get("start_frame", 0))
	_build_overlay(with_background)
	print("SHOWREEL_BEGIN %s %d %d" % [chapter_id, _frame_index, int(_chapter.get("frames", 0))])
	return _chapter


## 本章录完：打印帧号对账行并交给 `TestEntry` 关进程。
func _end_chapter() -> void:
	var expected_end := int(_chapter.get("start_frame", 0)) + int(_chapter.get("frames", 0)) - 1
	print("SHOWREEL_END %s %d" % [chapter_id, _frame_index - 1])
	_expect(
			_frame_index - 1 == expected_end,
			"章节 %s 该录到第 %d 帧，实际停在第 %d 帧" % [chapter_id, expected_end, _frame_index - 1],
		)
	get_tree().quit(0)


func _load_timeline() -> Dictionary:
	var path := ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with(TIMELINE_ARGUMENT_PREFIX):
			path = argument.trim_prefix(TIMELINE_ARGUMENT_PREFIX)
	_expect(not path.is_empty(), "要传 %s<路径>" % TIMELINE_ARGUMENT_PREFIX)
	if path.is_empty():
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	_expect(parsed is Dictionary, "timeline.json 要能解析成字典")
	if not (parsed is Dictionary):
		return {}
	return parsed


## 按镜头 id 取 timeline 里的帧数；找不到就按 0 帧处理，由 `_expect` 判红。
func _shot_frames(shot_id: StringName) -> int:
	for shot: Dictionary in _chapter.get("shots", []):
		if StringName(shot.get("id", "")) == shot_id:
			return int(shot.get("frames", 0))
	_expect(false, "章节 %s 的 timeline 里没有镜头 %s" % [chapter_id, shot_id])
	return 0


## 录一个镜头：[param update] 每帧按 0–1 的镜头进度调用一次，镜头动作写在那里。
func _record_shot(shot_id: StringName, caption: String, update: Callable = Callable()) -> void:
	var frame_count := _shot_frames(shot_id)
	if frame_count <= 0:
		return
	_caption_label.text = caption
	print("SHOWREEL_SHOT %s %d %d" % [shot_id, _frame_index, frame_count])
	for step in frame_count:
		if update.is_valid():
			update.call(float(step) / float(maxi(frame_count - 1, 1)))
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		_expect(_save_frame(), "第 %d 帧该落盘" % _frame_index)
		_frame_index += 1


func _save_frame() -> bool:
	var path := "%s/%06d.jpg" % [ProjectSettings.globalize_path(frames_directory), _frame_index]
	return get_viewport().get_texture().get_image().save_jpg(path, 0.92) == OK


## 字幕层：深色底（可选）、左上章节标题、底部中文字幕、右上进度。
func _build_overlay(with_background: bool) -> void:
	var layer := CanvasLayer.new()
	layer.layer = 100
	layer.name = "ShowreelOverlay"
	add_child(layer)
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	_overlay_root = root
	if with_background:
		var background := ColorRect.new()
		background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		background.color = BACKGROUND_COLOR
		background.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root.add_child(background)
	var subtitle_font := _subtitle_font()
	_subtitle_font_resource = subtitle_font
	_title_label = _make_label(root, "Title", subtitle_font, TITLE_FONT_SIZE, Color(0.98, 0.97, 0.93))
	_title_label.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	_title_label.position = Vector2(48, 32)
	_title_label.text = chapter_title
	_progress_label = _make_label(
			root, "Progress", subtitle_font, PROGRESS_FONT_SIZE, Color(0.85, 0.86, 0.8),
		)
	_progress_label.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	_progress_label.position = Vector2(-220, 40)
	_progress_label.size = Vector2(172, 32)
	_progress_label.text = "%d / %d" % [_chapter_ordinal, _chapter_count]
	_progress_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	var bar := ColorRect.new()
	bar.name = "CaptionBar"
	bar.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	bar.offset_left = 0
	bar.offset_right = 0
	bar.offset_top = -132
	bar.offset_bottom = -28
	bar.color = Color(0.04, 0.05, 0.06, 0.84)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(bar)
	_caption_label = _make_label(root, "Caption", subtitle_font, CAPTION_FONT_SIZE, Color(1, 1, 1))
	_caption_label.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	_caption_label.offset_left = 56
	_caption_label.offset_right = -56
	_caption_label.offset_top = -126
	_caption_label.offset_bottom = -34
	_caption_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caption_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_caption_label.text = ""


## 片头片尾卡这类纯文字画面用：在字幕层正中加一行大字（竖直位置按 [param center_offset] 调）。
func _add_center_label(text: String, font_size: int, center_offset: float = 0.0) -> Label:
	var label := _make_label(
			_overlay_root, "Center", _subtitle_font_resource, font_size, Color(1, 0.98, 0.94),
		)
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	label.offset_top = center_offset
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.text = text
	return label


func _make_label(
		parent: Control, label_name: String, font: Font, font_size: int, color: Color,
	) -> Label:
	var label := Label.new()
	label.name = label_name
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_override(&"font", font)
	label.add_theme_font_size_override(&"font_size", font_size)
	label.add_theme_color_override(&"font_color", color)
	label.add_theme_color_override(&"font_shadow_color", Color(0, 0, 0, 0.85))
	label.add_theme_constant_override(&"shadow_offset_x", 3)
	label.add_theme_constant_override(&"shadow_offset_y", 3)
	label.add_theme_constant_override(&"shadow_outline_size", 2)
	parent.add_child(label)
	return label


## 字幕字体：优先用项目自己的 UI 字体；这里用系统字体兜底（示例：雅黑 → 雅黑 UI → 黑体）。
func _subtitle_font() -> Font:
	var system_font := SystemFont.new()
	system_font.font_names = PackedStringArray([
			"Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "SimSun",
		])
	return system_font


## 章节里摆镜头：把相机焦点在两格之间按 t 线性插值（世界坐标里插，避免格子量化的台阶）。
## 参数不写死类型；目标项目换成自己的相机/网格封装即可。
func _pan_camera(
		camera: Node3D, grid: Node, from_tile: Vector2, to_tile: Vector2, t: float,
	) -> void:
	var from_position: Vector3 = grid.to_global(grid.tile_center_position(Vector2i(from_tile)))
	var to_position: Vector3 = grid.to_global(grid.tile_center_position(Vector2i(to_tile)))
	camera.position = from_position.lerp(to_position, t)


## 关掉一切会跟脚本抢镜头的输入：边缘滚动、世界输入与整屏像素吸附后的抖动都不该出现在片子里。
## 属性名按目标项目的相机实现改。
func _take_camera_control(camera: Node3D) -> void:
	camera.set("edge_scroll_enabled", false)
	camera.set("world_input_enabled", false)


## 换一档视野：档位 setter 在「档位没变」时直接返回，所以先多摆一档再切回来。
## 档位属性名按目标项目的相机实现改。
func _set_zoom(camera: Node3D, visible_tiles: float) -> void:
	camera.set("zoom_sizes", PackedFloat32Array([visible_tiles, visible_tiles]))
	camera.set("zoom_step_index", 1)
	camera.set("zoom_step_index", 0)
