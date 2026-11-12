extends "res://.export/showreel/capture_base.gd"
## 示例：在真实主场景里录一章（内容取自一个城市建造游戏：果园成熟、市场采购员、顶栏读数、
## 住宅区与事件公告），不是摆拍图。复制后把 .export/showreel 换成自己的 <WORK_DIR>，
## 并把 GameSession/GameUi/IsometricCamera/TileGrid/GameClock 等换成目标项目的封装。

const HUT_ID := &"gardeners_hut"
const OLIVE_ID := &"olive_tree"
const VINE_ID := &"grape_vine"
const GRANARY_ID := &"granary"
const ROAD_LENGTH := 6
const TREASURY_DRACHMAS := 200000
## 固定地块（坐标取自示例项目的一个预览脚本）：测试小图是 96×96 平地，这一块一定放得下市场。
const MARKET_ORIGIN := Vector2i(40, 42)
const OLIVE_PERCENTS: Array[float] = [0.0, 40.0, 70.0, 100.0]
const VINE_PERCENTS: Array[float] = [0.0, 60.0, 100.0]
const SHOT_ZOOM_IN_TILES := 13.0
const GROVE_ZOOM_IN_TILES := 7.0

var _session: GameSession
var _ui: GameUi
var _camera: IsometricCamera
var _grid: TileGrid
var _clock: GameClock
var _road_view: Node
var _hut_tile := SharedConstants.NO_TILE
var _market_tile := SharedConstants.NO_TILE
var _road_origin := SharedConstants.NO_TILE
var _shot_progress := 0.0
var _event_posted := false


func _ready() -> void:
	_start_chapter(&"ch4_simulation", false)
	_session = await _open_test_world()
	_ui = _test_world_root.get_node(^"%GameUi") as GameUi
	_camera = _test_world_root.get_node(^"%IsometricCamera") as IsometricCamera
	_grid = _test_world_root.get_node(^"%TileGrid") as TileGrid
	_road_view = _test_world_root.get_node(^"%RoadView")
	_clock = _test_world_root.get_node(^"%GameClock") as GameClock
	_clock.is_auto_ticking = false
	_take_camera_control(_camera)
	_session.labor_finance.add_treasury_drachmas(
			TREASURY_DRACHMAS, LaborFinanceSimulation.REASON_ADJUSTMENT,
		)
	_place_grove()
	_place_market()
	await _record_shot(&"grove", "果园与麦场按格生长，逐棵成熟 #111 #194", _grove_update)
	await _record_shot(&"customers", "市场顾客跟队，街上不再有通勤小人 #209 #245", _customers_update)
	await _record_shot(
			&"autosave", "自动存档 5 档轮转，顶栏读数当场刷新 #232 #233 #237", _autosave_update,
		)
	await _record_shot(&"migration", "迁入者走进住宅占地，移民不再要求道路连通 #246 #248", _migration_update)
	await _record_shot(&"event", "事件改成阻塞性公告弹窗 #213", _event_update)
	await _end_chapter()


## 果园：园丁小屋 + 四棵橄榄 + 三棵葡萄，成熟度摆在不同档上，重建一次树上实例。
func _place_grove() -> void:
	_hut_tile = _find_placeable_tile(HUT_ID, map_center_tile(_grid.terrain), BuildingMeshes.footprint_of(HUT_ID))
	_expect(_hut_tile != SharedConstants.NO_TILE, "园丁小屋要找到空位")
	_expect(_session.build(HUT_ID, _hut_tile), "园丁小屋要放得下")
	var tree_tiles: Array[Vector2i] = []
	for index in OLIVE_PERCENTS.size():
		var tile := _find_placeable_tile(
				OLIVE_ID, _hut_tile + Vector2i(2 + index, 0), Vector2i(1, 1),
			)
		_expect(tile != SharedConstants.NO_TILE, "第 %d 棵橄榄树要找到空位" % (index + 1))
		_expect(_session.build(OLIVE_ID, tile), "第 %d 棵橄榄树要种得下" % (index + 1))
		tree_tiles.append(tile)
	for index in VINE_PERCENTS.size():
		var tile := _find_placeable_tile(
				VINE_ID, _hut_tile + Vector2i(2 + index, 2), Vector2i(1, 1),
			)
		_expect(tile != SharedConstants.NO_TILE, "第 %d 棵葡萄藤要找到空位" % (index + 1))
		_expect(_session.build(VINE_ID, tile), "第 %d 棵葡萄藤要种得下" % (index + 1))
		tree_tiles.append(tile)
	for index in tree_tiles.size():
		var occupancy := _session.build_system.occupancy_at(tree_tiles[index])
		if occupancy == null:
			continue
		var percent := OLIVE_PERCENTS[index] if index < OLIVE_PERCENTS.size() else VINE_PERCENTS[
				index - OLIVE_PERCENTS.size()
			]
		_session.grove.set_maturity_percent(occupancy.id, percent)
	(_test_world_root.get_node(^"%GroveView") as GroveView).rebuild_trees()


## 市场：一条南北向的路加上一座市场与四个摊位，采购员就在这条路上来回。
func _place_market() -> void:
	for row in ROAD_LENGTH:
		_expect(
				_session.build(&"road", MARKET_ORIGIN + Vector2i(2, row)),
				"市场旁的路要能铺上",
			)
	_market_tile = MARKET_ORIGIN
	_road_origin = MARKET_ORIGIN + Vector2i(2, 0)
	_expect(_session.build(&"market", _market_tile), "市场要放得下")
	var market := _session.build_system.market_at(_market_tile)
	_expect(market != null, "市场要登记进建造层")
	if market == null:
		return
	var slots := _session.build_system.market_slot_rects(market)
	var stall_ids: Array[StringName] = [
		&"market_stall_food", &"market_stall_fleece", &"market_stall_olive_oil", &"market_stall_wine",
	]
	for index in mini(slots.size(), stall_ids.size()):
		_expect(_session.build(stall_ids[index], slots[index].position), "摊位要放得下")
	_session.mark_refreshed()


## 果园镜头：贴着三排植物慢慢横移，成熟度差异一屏看完。
func _grove_update(t: float) -> void:
	_shot_progress = _ease(t)
	_set_zoom(_camera, GROVE_ZOOM_IN_TILES)
	_pan_camera(
			_camera,
			_grid,
			Vector2(_hut_tile + Vector2i(1, 2)),
			Vector2(_hut_tile + Vector2i(6, 2)),
			_shot_progress,
		)


## 采购员镜头：市场与摊位在画面里，路上有采购员来回走（每帧推一拍让它动起来）。
func _customers_update(t: float) -> void:
	_shot_progress = _ease(t)
	_set_zoom(_camera, SHOT_ZOOM_IN_TILES)
	_pan_camera(
			_camera,
			_grid,
			Vector2(_market_tile + Vector2i(-1, 1)),
			Vector2(_market_tile + Vector2i(2, 1)),
			_shot_progress,
		)
	if int(t * 90.0) % 12 == 0:
		_session.walker_simulation.spawn(
				_road_origin + Vector2i(0, ROAD_LENGTH - 1),
				_road_origin,
				null,
				WalkerSimulation.WalkerKind.PURCHASER,
			)
	_tick_once(_road_view, 1.0 / 30.0)


## 顶栏镜头：把拍长压到很小让时钟快跑，顶栏的资源读数当场往下跳。
func _autosave_update(t: float) -> void:
	_shot_progress = _ease(t)
	_use_tick_seconds(0.05)
	_clock.is_auto_ticking = true
	_set_zoom(_camera, SHOT_ZOOM_IN_TILES * 1.2)
	_pan_camera(
			_camera,
			_grid,
			Vector2(_market_tile + Vector2i(3, 2)),
			Vector2(_market_tile + Vector2i(1, 2)),
			_shot_progress,
		)


## 住宅区镜头：沿着一排住宅横移，迁入者走进住宅占地。
func _migration_update(t: float) -> void:
	_shot_progress = _ease(t)
	_use_tick_seconds(0.05)
	_set_zoom(_camera, SHOT_ZOOM_IN_TILES)
	_pan_camera(
			_camera,
			_grid,
			Vector2(_market_tile + Vector2i(-6, -6)),
			Vector2(_market_tile + Vector2i(-2, -6)),
			_shot_progress,
		)


## 事件镜头：走真实消息路由，公告弹窗把整棵树停住（阻塞性），镜头仍在缓慢推近。
func _event_update(t: float) -> void:
	_shot_progress = _ease(t)
	if not _event_posted:
		_event_posted = true
		_session._message_router.on_random_event_triggered(
				&"global_harvest",
				AdventureRules.EVENT_EFFECT_GOODS,
				&"wheat",
				0,
				12,
			)
	_set_zoom(_camera, SHOT_ZOOM_IN_TILES * 0.9)
	_pan_camera(
			_camera,
			_grid,
			Vector2(_market_tile),
			Vector2(_market_tile + Vector2i(1, 0)),
			_shot_progress,
		)


## 从给定点向外找一块空地下这座建筑；找不到回 NO_TILE。
func _find_placeable_tile(
		building_id: StringName, center_tile: Vector2i, footprint_size: Vector2i,
	) -> Vector2i:
	var terrain := _grid.terrain
	for radius in range(0, 24):
		for tile_y in range(-radius, radius + 1):
			for tile_x in range(-radius, radius + 1):
				if maxi(absi(tile_x), absi(tile_y)) != radius:
					continue
				var origin := center_tile + Vector2i(tile_x, tile_y)
				if not terrain.is_inside(origin):
					continue
				if not terrain.is_inside(origin + footprint_size - Vector2i.ONE):
					continue
				if _is_buildable_block(terrain, origin, footprint_size) and (
						_session.build_system.can_place(building_id, origin)
					):
					return origin
	return SharedConstants.NO_TILE


static func _ease(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)
