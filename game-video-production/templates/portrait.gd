extends Node3D
## 渲染 256×256 的说话人头像（头肩特写），供字幕条左侧使用。
##
## 用法：
##   godot --path . res://.export/<slug>/portrait.tscn -- \
##       --model=res://app/<片名>/assets/foo.glb --out=res://.export/<slug>/avatars/Alex.png
##   godot --path . ... -- --who=Judge --model=... --out=...
##
## 关键：浅灰背景 + 强主光。深色背景会让深色衣服在黑白后处理里糊成一团。

const SIZE := 256


func _ready() -> void:
	get_window().size = Vector2i(SIZE, SIZE)
	var args := {}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--"):
			var pair := argument.substr(2).split("=", true, 1)
			args[pair[0]] = pair[1] if pair.size() > 1 else ""
	var model_path: String = args.get("model", "")
	var out_path: String = args.get("out", "res://.export/avatar.png")
	if model_path == "":
		push_error("缺少 --model")
		get_tree().quit(1)
		return
	var env := Environment.new()
	env.background_mode = 1
	env.background_color = Color(0.82, 0.82, 0.82)
	env.ambient_light_source = 2
	env.ambient_light_color = Color(0.85, 0.85, 0.85)
	env.ambient_light_energy = 1.15
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-24.0, 28.0, 0.0)
	key.light_energy = 3.0
	key.light_color = Color(1.0, 0.95, 0.88)
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-12.0, -130.0, 0.0)
	fill.light_energy = 0.9
	fill.light_color = Color(0.78, 0.82, 1.0)
	add_child(fill)
	var scene: PackedScene = load(model_path)
	var holder := Node3D.new()
	add_child(holder)
	holder.add_child(scene.instantiate())
	var camera := Camera3D.new()
	camera.position = Vector3(0.0, 1.52, 0.95)
	camera.fov = 38.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.0, 1.42, 0.0), Vector3.UP)
	for _i in 4:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_path.get_base_dir()))
	get_viewport().get_texture().get_image().save_png(out_path)
	print("PORTRAIT %s" % ProjectSettings.globalize_path(out_path))
	get_tree().quit()
