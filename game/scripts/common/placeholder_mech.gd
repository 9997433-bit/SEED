extends Node3D
## 原创方块占位机体。
##
## 全部由引擎自带的 BoxMesh 在运行时拼装，不含任何官方模型、贴图或骨骼。
## 数据侧 asset_binding.placeholder 为 true 的条目，在 M0 一律由本节点代表。

@export var primary_color := Color(0.29, 0.55, 0.94)
@export var frame_color := Color(0.21, 0.24, 0.31)
@export var accent_color := Color(0.95, 0.72, 0.22)
## 展示台上的自转速度；设为 0 可静止观察。
@export var idle_spin_deg_per_sec := 12.0

func _ready() -> void:
	_build()

func _process(delta: float) -> void:
	if not is_zero_approx(idle_spin_deg_per_sec):
		rotate_y(deg_to_rad(idle_spin_deg_per_sec) * delta)

func _build() -> void:
	var primary := _make_material(primary_color, 0.45)
	var frame := _make_material(frame_color, 0.7)
	var accent := _make_material(accent_color, 0.25, 0.6)

	_add_box("Pelvis", Vector3(1.0, 0.5, 0.7), Vector3(0.0, 1.85, 0.0), frame)
	_add_box("Torso", Vector3(1.4, 1.05, 0.8), Vector3(0.0, 2.6, 0.0), primary)
	_add_box("ChestVent", Vector3(0.5, 0.34, 0.1), Vector3(0.0, 2.7, 0.44), accent)
	_add_box("Neck", Vector3(0.3, 0.16, 0.3), Vector3(0.0, 3.2, 0.0), frame)
	_add_box("Head", Vector3(0.46, 0.42, 0.46), Vector3(0.0, 3.45, 0.0), primary)
	_add_box("Visor", Vector3(0.36, 0.1, 0.06), Vector3(0.0, 3.47, 0.24), accent)
	_add_box("Backpack", Vector3(0.9, 0.72, 0.34), Vector3(0.0, 2.7, -0.55), frame)

	for side in [-1.0, 1.0]:
		var tag := "L" if side < 0.0 else "R"
		_add_box("Shoulder" + tag, Vector3(0.52, 0.5, 0.62), Vector3(side * 0.98, 2.78, 0.0), primary)
		_add_box("UpperArm" + tag, Vector3(0.3, 0.66, 0.3), Vector3(side * 0.98, 2.2, 0.0), frame)
		_add_box("Forearm" + tag, Vector3(0.34, 0.7, 0.34), Vector3(side * 0.98, 1.6, 0.0), primary)
		_add_box("Thigh" + tag, Vector3(0.42, 0.9, 0.46), Vector3(side * 0.34, 1.3, 0.0), primary)
		_add_box("Shin" + tag, Vector3(0.38, 0.9, 0.4), Vector3(side * 0.34, 0.45, 0.0), frame)
		_add_box("Foot" + tag, Vector3(0.5, 0.2, 0.82), Vector3(side * 0.34, 0.1, 0.1), primary)
		_add_box("Thruster" + tag, Vector3(0.22, 0.5, 0.22), Vector3(side * 0.3, 2.25, -0.64), accent)

	# 主兵装占位：与 data/weapons/ 的 weapon.beam_rifle_standard 对应的空盒子。
	_add_box("MainWeapon", Vector3(0.22, 0.22, 1.3), Vector3(0.98, 1.35, 0.42), frame)

func _add_box(part_name: String, size: Vector3, offset: Vector3, material: StandardMaterial3D) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	var part := MeshInstance3D.new()
	part.name = part_name
	part.mesh = mesh
	part.position = offset
	part.material_override = material
	add_child(part)

func _make_material(color: Color, roughness: float, emission_energy := 0.0) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	material.metallic = 0.1
	if emission_energy > 0.0:
		material.emission_enabled = true
		material.emission = color
		material.emission_energy_multiplier = emission_energy
	return material
