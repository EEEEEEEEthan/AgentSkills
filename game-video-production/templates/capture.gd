extends Node
## 逐帧录制器：按 timeline.json 把每个镜头在 1/30 秒的步长上推进并落盘成 JPG。
##
## 整片：
##   godot --path . --disable-vsync --fixed-fps 30 res://.export/<slug>/capture.tscn -- \
##       --film=res://app/<片名>/film.tscn --timeline=res://.export/<slug>/timeline.json
## 单帧预览（摆机位、查字幕用，比重录整片快一百倍）：
##   ... --film=... --timeline=... --still=<镜头 id>:<进度 0–1>
##
## 导演场景需要实现：
##   show_shot(id, t) / set_speaker(who) / set_tag(text) / set_caption(text, index, total)

const FRAME_DIR := "res://.export/frames"


func _ready() -> void:
	get_window().size = Vector2i(1280, 720)
	var args := _parse_args()
	var film: Node3D = load(args["film"]).instantiate()
	add_child(film)
	await get_tree().process_frame
	await get_tree().process_frame
	if args.has("still"):
		await _save_still(film, args["still"], args.get("timeline", ""))
	else:
		await _record(film, JSON.parse_string(FileAccess.get_file_as_string(args["timeline"])))
	get_tree().quit()


func _record(film: Node3D, timeline: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FRAME_DIR))
	var shots: Array = timeline["shots"]
	var total_shots: int = int(timeline.get("total_shots", shots.size()))
	var written := 0
	for shot in shots:
		var shot_id: String = shot["id"]
		var start: int = shot["start"]
		var count: int = shot["frames"]
		print("SHOWREEL_BEGIN %s %d %d" % [shot_id, start, count])
		for index in count:
			var progress := float(index) / float(maxi(count - 1, 1))
			film.show_shot(shot_id, progress)
			film.set_speaker(shot.get("who", ""))
			film.set_tag(shot.get("tag", ""))
			film.set_caption(shot.get("caption", ""), shot["index"], total_shots)
			await get_tree().process_frame
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_jpg(
				"%s/%06d.jpg" % [FRAME_DIR, start + index], 0.9
			)
			written += 1
			if written % 120 == 0:
				print("PROGRESS %d / %d" % [written, timeline["total_frames"]])
		print("SHOWREEL_END %s %d" % [shot_id, start + count - 1])
	print("SHOWREEL_DONE %d" % written)


func _save_still(film: Node3D, spec: String, timeline_path: String) -> void:
	var parts := spec.split(":")
	var shot_id := parts[0]
	var progress := float(parts[1]) if parts.size() > 1 else 0.0
	film.show_shot(shot_id, progress)
	var caption := ""
	var who := ""
	var tag := ""
	if timeline_path != "":
		var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(timeline_path))
		for shot in timeline["shots"]:
			if shot["id"] == shot_id:
				caption = shot.get("caption", "")
				who = shot.get("who", "")
				tag = shot.get("tag", "")
				break
	film.set_speaker(who)
	film.set_tag(tag)
	film.set_caption(caption, 1, 1)
	for _i in 4:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path := "res://.export/still_%s_%02d.jpg" % [shot_id, int(progress * 100)]
	get_viewport().get_texture().get_image().save_jpg(path, 0.92)
	print("STILL %s" % ProjectSettings.globalize_path(path))


func _parse_args() -> Dictionary:
	var args := {}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--"):
			var pair := argument.substr(2).split("=", true, 1)
			args[pair[0]] = pair[1] if pair.size() > 1 else ""
	return args
