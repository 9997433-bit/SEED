extends Node3D
## M0 标题场景。
##
## 职责仅限于证明工程骨架可运行：占位 3D 机体 + 标题 UI + 数据构建产物载入。
## 战斗、任务与养成在 M1 之后接入（见 docs/REMAKE-PLAN.md 六、里程碑）。

const UnitCatalogScript := preload("res://scripts/data/unit_catalog.gd")

@onready var _status: Label = $UI/Root/Margin/Layout/Status
@onready var _catalog_panel: PanelContainer = $UI/Root/CatalogPanel
@onready var _catalog_list: VBoxContainer = $UI/Root/CatalogPanel/Pad/Body/Scroll/CatalogList
@onready var _sortie_button: Button = $UI/Root/Margin/Layout/Buttons/SortieButton
@onready var _catalog_button: Button = $UI/Root/Margin/Layout/Buttons/CatalogButton
@onready var _quit_button: Button = $UI/Root/Margin/Layout/Buttons/QuitButton

var _catalog := UnitCatalogScript.new()
var _catalog_built := false

func _ready() -> void:
	_sortie_button.pressed.connect(_on_sortie_pressed)
	_catalog_button.pressed.connect(_on_catalog_pressed)
	_quit_button.pressed.connect(_on_quit_pressed)

	if _catalog.load_index():
		_status.text = "数据管线：已载入 %d 台底盘 / %d 个形态 / %d 件武装（balance_patch %s）" % [
			int(_catalog.counts.get("chassis", 0)),
			int(_catalog.counts.get("forms", 0)),
			int(_catalog.counts.get("weapons", 0)),
			_catalog.balance_patch,
		]
	else:
		_status.text = "数据管线：%s" % _catalog.error
		_catalog_button.disabled = true

func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("ui_cancel"):
		return
	if _catalog_panel.visible:
		_catalog_panel.hide()
	else:
		get_tree().quit()
	get_viewport().set_input_as_handled()

func _on_sortie_pressed() -> void:
	_status.text = "出击流程在 M1 实装：M0 只交付工程骨架、占位机体与数据校验管线。"

func _on_catalog_pressed() -> void:
	if not _catalog_built:
		_build_catalog()
	_catalog_panel.visible = not _catalog_panel.visible

func _on_quit_pressed() -> void:
	get_tree().quit()

func _build_catalog() -> void:
	for entry in _catalog.chassis:
		var row := Label.new()
		row.text = _catalog.summary_line(entry)
		row.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_catalog_list.add_child(row)
	_catalog_built = true
