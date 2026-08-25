extends RefCounted
## 载入数据构建产物（units_index.json），供 UI 只读展示。
##
## 数据源始终是 data/**.yaml；构建产物由
## `python3 tools/data_validator/validate.py --emit-index game/data_build/units_index.json`
## （或 `make validate-data`）生成，M0 因此不需要在 GDScript 里解析 YAML。

const INDEX_PATH := "res://data_build/units_index.json"

var loaded := false
var error := ""
var milestone := ""
var balance_patch := ""
var counts := {}
var factions := {}
var chassis: Array = []

func load_index(path := INDEX_PATH) -> bool:
	var data := _read_index(path)
	if data.is_empty():
		if error.is_empty():
			error = "未找到数据构建产物 %s，请先运行 make validate-data" % path
		return false

	milestone = str(data.get("milestone", ""))
	balance_patch = str(data.get("balance_patch", ""))
	counts = data.get("counts", {})
	chassis = data.get("chassis", [])
	for faction in data.get("factions", []):
		factions[faction.get("id", "")] = faction.get("display_name", "")
	loaded = true
	return true

## 单台底盘的一行摘要，例如「GAT-X105  强袭 · 3 形态 · 地球联合军 · 换装」。
func summary_line(entry: Dictionary) -> String:
	var forms: Array = entry.get("forms", [])
	var mechanics: Array[String] = []
	if _has_form_type(forms, "equipment_form"):
		mechanics.append("换装")
	if _has_transform(forms):
		mechanics.append("变形")
	if _has_overlays(forms):
		mechanics.append("装甲/模式")

	var faction_id := str(entry.get("faction_playable", ""))
	var parts: Array[String] = [
		"%d 形态" % forms.size(),
		str(factions.get(faction_id, faction_id)),
	]
	if not mechanics.is_empty():
		parts.append("、".join(mechanics))
	return "%s  %s · %s" % [
		str(entry.get("model_number", "?")),
		str(entry.get("display_name", "?")),
		" · ".join(parts),
	]

func _has_form_type(forms: Array, form_type: String) -> bool:
	for form in forms:
		if form.get("type", "") == form_type:
			return true
	return false

func _has_transform(forms: Array) -> bool:
	for form in forms:
		if not (form.get("transform_targets", []) as Array).is_empty():
			return true
	return false

func _has_overlays(forms: Array) -> bool:
	for form in forms:
		if not (form.get("mode_overlays", []) as Array).is_empty():
			return true
	return false

func _read_index(path: String) -> Dictionary:
	var text := ""
	if FileAccess.file_exists(path):
		text = FileAccess.get_file_as_string(path)
	if text.is_empty() and ResourceLoader.exists(path):
		# 导出版中 .json 会被作为 JSON 资源导入，此时读不到原始文本。
		var resource := ResourceLoader.load(path)
		if resource is JSON and typeof(resource.data) == TYPE_DICTIONARY:
			return resource.data
	if text.is_empty():
		return {}

	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		error = "构建产物不是合法 JSON 对象：%s" % path
		return {}
	return parsed
