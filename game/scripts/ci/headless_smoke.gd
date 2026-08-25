extends SceneTree
## CI 冒烟检查：headless 载入主场景并跑若干帧，确认工程骨架与数据管线没有断。
##
## 由 .github/workflows/build-pc.yml 以
## `godot --headless --path game --script res://scripts/ci/headless_smoke.gd` 调用。
## 只做断言与打印，不含任何玩法逻辑。

const UnitCatalogScript := preload("res://scripts/data/unit_catalog.gd")

const MAIN_SCENE := "res://scenes/bridge/title_screen.tscn"
const FRAMES := 120

## 数据构建产物至少应有的规模，防止 units_index.json 被清空或截断后 CI 仍然放行。
const MIN_CHASSIS := 18
const MIN_FORMS := 29
const MIN_WEAPONS := 27

var _frames := 0
var _failed := false

func _initialize() -> void:
	if not _check_data_index():
		return
	if not _check_settings_autoload():
		return
	if not _spawn_main_scene():
		return
	print("SMOKE: 主场景已实例化，开始跑 %d 帧" % FRAMES)

func _process(_delta: float) -> bool:
	if _failed:
		return true
	_frames += 1
	if _frames < FRAMES:
		return false
	print("SMOKE: OK — 主场景运行 %d 帧无脚本错误" % _frames)
	return true

func _check_data_index() -> bool:
	var catalog := UnitCatalogScript.new()
	if not catalog.load_index():
		return _fail("数据构建产物载入失败：%s" % catalog.error)

	var chassis_count := int(catalog.counts.get("chassis", 0))
	var form_count := int(catalog.counts.get("forms", 0))
	var weapon_count := int(catalog.counts.get("weapons", 0))
	if chassis_count < MIN_CHASSIS or form_count < MIN_FORMS or weapon_count < MIN_WEAPONS:
		return _fail("数据构建产物规模异常：%d 底盘 / %d 形态 / %d 武装" % [
			chassis_count, form_count, weapon_count,
		])
	if catalog.chassis.size() != chassis_count:
		return _fail("底盘条目数与 counts 不一致：%d vs %d" % [
			catalog.chassis.size(), chassis_count,
		])

	print("SMOKE: 数据管线 OK — %d 底盘 / %d 形态 / %d 武装（balance_patch %s）" % [
		chassis_count, form_count, weapon_count, catalog.balance_patch,
	])
	return true

func _check_settings_autoload() -> bool:
	var settings := root.get_node_or_null("Settings")
	if settings == null:
		return _fail("Settings autoload 未注册（检查 project.godot [autoload]）")
	if not settings.set_locale("en"):
		return _fail("Settings.set_locale(\"en\") 失败")
	if not settings.set_volume("master", 0.5):
		return _fail("Settings.set_volume(\"master\", 0.5) 失败")
	settings.reset_to_defaults()
	print("SMOKE: Settings autoload OK — %s" % JSON.stringify(settings.snapshot()))
	return true

func _spawn_main_scene() -> bool:
	var packed: PackedScene = load(MAIN_SCENE)
	if packed == null:
		return _fail("主场景载入失败：%s" % MAIN_SCENE)
	var scene := packed.instantiate()
	if scene == null:
		return _fail("主场景实例化失败：%s" % MAIN_SCENE)
	root.add_child(scene)
	return true

func _fail(message: String) -> bool:
	push_error("SMOKE FAILED: %s" % message)
	printerr("SMOKE FAILED: %s" % message)
	_failed = true
	quit(1)
	return false
