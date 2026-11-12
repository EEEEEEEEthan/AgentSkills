extends Node
## 示例项目里这里继承的是 TestScriptBase（测试入口）；复制后改成项目自己的测试/场景基类。
## 字幕宽度体检：用录制时同一个字体量每条字幕的像素宽度，
## 超过底条可用宽度（1280 − 2×56 = 1168）的会打 WIDE，供重录前确认。

const CAPTION_FONT_SIZE := 30
const AVAILABLE_WIDTH := 1168.0
## 改成自己的 <WORK_DIR>/timeline.json。
const TIMELINE_PATH := "res://.export/showreel/timeline.json"


func _ready() -> void:
	var font := SystemFont.new()
	font.font_names = PackedStringArray([
			"Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "SimSun",
		])
	var parsed: Variant = JSON.parse_string(
			FileAccess.get_file_as_string(TIMELINE_PATH)
		)
	if not (parsed is Dictionary):
		push_error("timeline.json 要能解析")
		get_tree().quit(1)
		return
	var widest := 0.0
	var widest_id := ""
	var over_count := 0
	for chapter: Dictionary in parsed["chapters"]:
		for shot: Dictionary in chapter["shots"]:
			var caption: String = shot["caption"]
			var width := font.get_string_size(
					caption, HORIZONTAL_ALIGNMENT_LEFT, -1, CAPTION_FONT_SIZE,
				).x
			if width > widest:
				widest = width
				widest_id = shot["id"]
			if width > AVAILABLE_WIDTH:
				over_count += 1
				print("WIDE %6.0f %s %s" % [width, shot["id"], caption])
	print("WIDEST %.0f %s  over_limit=%d" % [widest, widest_id, over_count])
	get_tree().quit(0)
