extends Node
## 全局设置（M0 占位）：音量与界面语言。
##
## M0 只做「读 / 改 / 存」这条链路，不涉及任何战斗、任务或养成逻辑。
## 画质档、键位自定义、锁敌模式等设置项在 M1+ 接入（见 docs/REMAKE-PLAN.md 四、技术架构）。

## 设置变更后广播，供 UI 与后续系统监听。
signal settings_changed(section: String, key: String, value: Variant)

const CONFIG_PATH := "user://settings.cfg"

## 音量分组 → 对应的音频总线名。M0 工程只有 Master 总线，
## Music / SFX 在音频管线落地前找不到总线时静默跳过。
const VOLUME_BUSES := {
	"master": "Master",
	"music": "Music",
	"sfx": "SFX",
}

## M0 支持的界面语言。日语（含官方术语口径）属于 Later，见 REMAKE-PLAN 七。
const SUPPORTED_LOCALES: PackedStringArray = ["zh_CN", "en"]

const DEFAULTS := {
	"audio": {
		"master": 0.8,
		"music": 0.7,
		"sfx": 0.8,
	},
	"locale": {
		"ui": "zh_CN",
	},
}

var _values := {}

## 值在 _init 阶段就位，autoload 之间互相读取设置时不依赖 _ready 顺序；
## 真正写入 AudioServer / TranslationServer 推迟到 _ready。
func _init() -> void:
	_values = _deep_copy_defaults()
	_load()

func _ready() -> void:
	_apply_all()

# --- 读 ---

func get_volume(group: String) -> float:
	return float(_values["audio"].get(group, 0.0))

func get_locale() -> String:
	return str(_values["locale"]["ui"])

## 设置项快照，便于 UI 或调试一次性读取。
func snapshot() -> Dictionary:
	return _deep_copy(_values)

# --- 写 ---

## 设置某个音量分组（0.0–1.0）。未知分组会被忽略并返回 false。
func set_volume(group: String, value: float) -> bool:
	if not VOLUME_BUSES.has(group):
		push_warning("未知音量分组：%s" % group)
		return false
	var clamped := clampf(value, 0.0, 1.0)
	if is_equal_approx(clamped, get_volume(group)):
		return true
	_values["audio"][group] = clamped
	_apply_volume(group)
	_save()
	settings_changed.emit("audio", group, clamped)
	return true

## 切换界面语言。不在 SUPPORTED_LOCALES 内则拒绝并返回 false。
func set_locale(locale: String) -> bool:
	if not SUPPORTED_LOCALES.has(locale):
		push_warning("未支持的界面语言：%s" % locale)
		return false
	if locale == get_locale():
		return true
	_values["locale"]["ui"] = locale
	_apply_locale()
	_save()
	settings_changed.emit("locale", "ui", locale)
	return true

## 恢复出厂设置。
func reset_to_defaults() -> void:
	_values = _deep_copy_defaults()
	_apply_all()
	_save()
	settings_changed.emit("", "", null)

# --- 应用 ---

func _apply_all() -> void:
	for group in VOLUME_BUSES:
		_apply_volume(group)
	_apply_locale()

func _apply_volume(group: String) -> void:
	var bus_index := AudioServer.get_bus_index(VOLUME_BUSES[group])
	if bus_index < 0:
		return
	var volume := get_volume(group)
	AudioServer.set_bus_mute(bus_index, is_zero_approx(volume))
	AudioServer.set_bus_volume_db(bus_index, linear_to_db(maxf(volume, 0.0001)))

func _apply_locale() -> void:
	TranslationServer.set_locale(get_locale())

# --- 持久化 ---

func _load() -> void:
	var config := ConfigFile.new()
	if config.load(CONFIG_PATH) != OK:
		return
	for group in VOLUME_BUSES:
		var raw: Variant = config.get_value("audio", group, _values["audio"].get(group, 0.0))
		if typeof(raw) == TYPE_FLOAT or typeof(raw) == TYPE_INT:
			_values["audio"][group] = clampf(float(raw), 0.0, 1.0)
	var locale := str(config.get_value("locale", "ui", get_locale()))
	if SUPPORTED_LOCALES.has(locale):
		_values["locale"]["ui"] = locale

func _save() -> void:
	var config := ConfigFile.new()
	for group in _values["audio"]:
		config.set_value("audio", group, _values["audio"][group])
	config.set_value("locale", "ui", get_locale())
	var err := config.save(CONFIG_PATH)
	if err != OK:
		push_warning("设置保存失败（%d）：%s" % [err, CONFIG_PATH])

func _deep_copy_defaults() -> Dictionary:
	return _deep_copy(DEFAULTS)

func _deep_copy(source: Dictionary) -> Dictionary:
	var out := {}
	for key in source:
		var value: Variant = source[key]
		out[key] = _deep_copy(value) if typeof(value) == TYPE_DICTIONARY else value
	return out
