extends "res://.export/showreel/capture_base.gd"
## 示例：自建夹具场景录一章（内容取自一个城市建造游戏的地形/水景）。
## 复制后把 .export/showreel 换成自己的 <WORK_DIR>，夹具与 TerrainView 等换成目标项目的封装。

const TERRAIN_ROWS: Array[String] = [
	"ggggggggg",
	"gwwwwgggg",
	"gwwwwgwwg",
	"gwwwwgggg",
	"ggwwggggg",
	"ggggggggg",
	"ggggggggg",
	"ggggggggg",
	"ggggggggg",
]
const HEIGHT_ROWS: Array[String] = [
	"000000000",
	"011111111",
	"011111111",
	"011110000",
	"000000000",
	"000000000",
	"000000000",
	"000000000",
	"000000000",
]
const SPILL_TILES: Array[Vector2i] = [Vector2i(2, 4), Vector2i(3, 4)]

var _camera: Camera3D


func _ready() -> void:
	_start_chapter(&"ch1_terrain", false)
	_build_world()
	await _record_shot(
			&"waterfall_wide",
			"水帘与挡水岩壁，水已成为一种地形类型 #230",
			_wide_update,
		)
	await _record_shot(
			&"waterfall_cliff",
			"崖顶水转角成岩，高地碎裂长出河口三角洲 #238",
			_cliff_update,
		)
	await _record_shot(
			&"waterfall_pull",
			"河岸碎石与草地坡，岩石坡道取代占位草坡 #217",
			_pull_update,
		)
	await _end_chapter()


func _build_world() -> void:
	var terrain := MapRowsFixture.create_with_rows(TERRAIN_ROWS, HEIGHT_ROWS)
	var sea_tiles: Array[Vector2i] = []
	for row in range(5, terrain.height_in_tiles):
		for column in terrain.width_in_tiles:
			terrain.set_terrain_type_at(Vector2i(column, row), MapTerrain.WATER_TERRAIN_ID)
			sea_tiles.append(Vector2i(column, row))
	for tile: Vector2i in SPILL_TILES:
		terrain.set_terrain_type_at(tile, MapTerrain.WATER_TERRAIN_ID)
		sea_tiles.append(tile)
	for tile: Vector2i in sea_tiles:
		terrain.refresh_edges_around(tile)
	terrain.apply_edit(sea_tiles)
	var world := Node3D.new()
	world.name = "TerrainWorld"
	add_child(world)
	# 地形视图要挂在树上一帧才会把网格建好，镜头等它。
	var view := (load("res://terrain/terrain_view.tscn") as PackedScene).instantiate() as TerrainView
	world.add_child(view)
	view.terrain = terrain
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-50, -35, 0)
	world.add_child(light)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color(0.42, 0.55, 0.66)
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(0.72, 0.74, 0.76)
	environment.environment.ambient_light_energy = 0.9
	world.add_child(environment)
	_camera = Camera3D.new()
	_camera.name = "ShowreelCamera"
	world.add_child(_camera)
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.size = 20.0
	_camera.far = 400.0
	_camera.global_position = Vector3(16.0, 9.0, 14.0)
	_camera.look_at(Vector3(4.2, 0.6, 3.6))
	_camera.current = true


## 全景：从东侧斜看整片湖与海，缓慢靠近。
func _wide_update(t: float) -> void:
	_shot_progress = _ease(t)
	_place_camera(
			Vector3(16.0, 9.0, 14.0),
			Vector3(11.4, 8.0, 12.2),
			Vector3(4.2, 0.6, 3.6),
			Vector3(4.4, 0.6, 3.6),
			lerpf(20.0, 16.5, t),
		)


## 水帘特写：贴着湖口往下推，水花与落水都在画面里。
func _cliff_update(t: float) -> void:
	_shot_progress = _ease(t)
	_place_camera(
			Vector3(5.8, 4.6, 7.6),
			Vector3(5.0, 3.9, 6.7),
			Vector3(2.5, 0.7, 4.3),
			Vector3(2.9, 0.5, 4.4),
			lerpf(9.5, 7.4, t),
		)


## 沿挡水崖壁与湖岸平推，最后拉开露出整片台地。
func _pull_update(t: float) -> void:
	_shot_progress = _ease(t)
	_place_camera(
			Vector3(6.2, 6.4, 4.4),
			Vector3(9.8, 7.4, 7.0),
			Vector3(6.2, 0.5, 2.4),
			Vector3(4.6, 0.5, 3.2),
			lerpf(10.0, 17.0, t),
		)


## 当前镜头进度（已缓动）：镜头插值只读这一份。
var _shot_progress := 0.0


func _place_camera(
		from_position: Vector3,
		to_position: Vector3,
		from_target: Vector3,
		to_target: Vector3,
		size: float,
	) -> void:
	_camera.global_position = _camera_curve(from_position, to_position)
	_camera.size = size
	_camera.look_at(_camera_curve(from_target, to_target))


func _camera_curve(from_point: Vector3, to_point: Vector3) -> Vector3:
	return from_point.lerp(to_point, _shot_progress)


static func _ease(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)
