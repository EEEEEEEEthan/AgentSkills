extends Node3D
## 导演脚本骨架。整场戏只由 show_shot(镜头 id, 进度 t) 算出来：
## 同一 t 永远得到同一帧，所以能单帧预览、能整片重录、能只重拍一场。

const SANTA_POS := Vector3(-1.4, 0.0, -6.0)
const SLEIGH_POS := Vector3(1.8, 0.0, -5.2)
const TRUCK_FROM := Vector3(-26.0, 0.0, -7.5)
const TRUCK_TO := Vector3(-7.5, 0.0, -4.2)

const AVATAR_DIR := "res://.export/avatars/"
var _anim: AnimationPlayer
var _avatars := {}
var _speakers := ["narrator", "alex", "horace"]


func _ready() -> void:
	_anim = %Santa.find_child("AnimationPlayer", true, false) as AnimationPlayer
	# 新 PNG 不经过导入管线：直接读文件，别用 load()。
	for who in _speakers:
		var path := ProjectSettings.globalize_path(AVATAR_DIR + who.capitalize() + ".png")
		if FileAccess.file_exists(path):
			_avatars[who] = ImageTexture.create_from_image(Image.load_from_file(path))
	reset_stage()


## 每次换镜头都先复位：位置、朝向、可见性、字幕卡、色调。
func reset_stage() -> void:
	%Santa.position = SANTA_POS
	%Santa.rotation = Vector3(0.0, deg_to_rad(-20.0), 0.0)
	%Sleigh.position = SLEIGH_POS
	%Marker.hide()
	%Title.hide()
	%TitleSub.hide()
	%Title.modulate.a = 1.0
	%TitleSub.modulate.a = 1.0


func show_shot(shot_id: String, t: float) -> void:
	reset_stage()
	match shot_id:
		"wide":
			_shot_wide(t)
		"close":
			_shot_close(t)
		"truck":
			_shot_truck(t)
		"endcard":
			_shot_endcard(t)
		_:
			_shot_wide(t)


func set_caption(text: String, shot_index: int, shot_total: int) -> void:
	var spoken := not text.strip_edges().is_empty()
	%Subtitle.text = text
	%SubBar.visible = spoken
	%Avatar.visible = spoken and %Avatar.texture != null
	%AvatarBorder.visible = %Avatar.visible
	if not spoken:
		%NameTag.visible = false
	%Index.text = "%02d / %02d" % [shot_index, shot_total]


func set_speaker(who: String) -> void:
	%Avatar.texture = _avatars.get(who, null)


func set_tag(text: String) -> void:
	%NameTag.text = text
	%NameTag.visible = not text.is_empty()


func show_title(headline: String, subline: String) -> void:
	%Title.text = headline
	%TitleSub.text = subline
	%Title.show()
	%TitleSub.show()


func _shot_wide(t: float) -> void:
	_aim(Vector3(2.2, 9.4, 27.0).lerp(Vector3(0.2, 5.0, 16.0), _smooth(t)), Vector3(0.0, 2.8, -17.0), lerpf(44.0, 40.0, t))
	_anim_time(2.0 + t * 4.0)


func _shot_close(t: float) -> void:
	_aim(Vector3(4.9, 2.55, 2.4).lerp(Vector3(3.2, 1.95, -0.6), _smooth(t)), Vector3(-0.4, 1.15, -5.8), lerpf(41.0, 37.0, t))
	_anim_time(1.0 + t * 5.0)


func _shot_truck(t: float) -> void:
	var progress := _smooth(t)
	%Truck.position = TRUCK_FROM.lerp(TRUCK_TO, progress)
	var direction := (TRUCK_TO - TRUCK_FROM).normalized()
	%Truck.rotation.y = atan2(direction.x, direction.z)   # 资产正面是 +z
	_aim(Vector3(1.0, 1.95, 1.2), %Truck.position + Vector3(0.0, 1.1, 0.0), 44.0)


func _shot_endcard(t: float) -> void:
	show_title("下期预告", "驯鹿去哪儿了")
	%Title.modulate.a = clampf(t / 0.18, 0.0, 1.0)
	%TitleSub.modulate.a = %Title.modulate.a
	_aim(Vector3(6.5, 3.6, 7.5).lerp(Vector3(0.0, 12.5, 31.0), _smooth(t)), Vector3(2.0, 4.0, -14.0), 46.0)


## 相机永远走这一条路：位置、注视点、fov 都是 t 的函数。
func _aim(camera_pos: Vector3, look_at_point: Vector3, fov: float) -> void:
	%Camera.position = camera_pos
	%Camera.look_at(look_at_point, Vector3.UP)
	%Camera.fov = fov


## 逐帧 seek，动画才是确定的；不要靠 play() 自己往下跑。
func _anim_time(seconds: float) -> void:
	if _anim == null:
		return
	_anim.play("Idle")
	_anim.seek(fmod(seconds, _anim.get_animation("Idle").length), true)
	_anim.pause()


func _smooth(t: float) -> float:
	var x := clampf(t, 0.0, 1.0)
	return x * x * (3.0 - 2.0 * x)
