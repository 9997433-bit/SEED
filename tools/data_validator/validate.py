#!/usr/bin/env python3
"""数据校验 CLI：对 data/ 下的 YAML 做 Schema 校验与跨条目引用完整性校验。

用法:
    python3 tools/data_validator/validate.py
    python3 tools/data_validator/validate.py --strict --format github
    python3 tools/data_validator/validate.py --emit-index game/data_build/units_index.json

退出码: 0 = 通过；1 = 存在 Error（--strict 时 Warning 也算失败）；2 = 用法或 IO 错误。

依赖: PyYAML 必需；jsonschema 可选（缺失时回退到内置的 JSON Schema 子集校验器，
覆盖本仓库 schema 实际用到的关键字）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import yaml
except ImportError:  # pragma: no cover - 环境问题，直接给出可执行的修复指引
    sys.stderr.write(
        "缺少 PyYAML。请先安装：pip install -r tools/data_validator/requirements.txt\n"
    )
    raise SystemExit(2)

if os.environ.get("SEED_VALIDATOR_FORCE_BUILTIN") == "1":
    jsonschema = None  # 便于 CI 同时回归内置子集校验器
else:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        jsonschema = None

REPO_ROOT = Path(__file__).resolve().parents[2]

ERROR = "error"
WARNING = "warning"
INFO = "info"

# 相对基准制：标准机动 MS 的 power_budget（docs/03-units-and-data.md 3.8.1）
POWER_BUDGET_BASELINE = 1000
POWER_BUDGET_TOLERANCE = 0.20
M0_EXPECTED_CHASSIS = 18


@dataclass
class Issue:
    level: str
    rule: str
    location: str
    message: str


@dataclass
class Document:
    """一个已加载的 YAML 源文件。"""

    kind: str
    rel_path: str
    data: Any


@dataclass
class Registry:
    """全部数据的解析结果，供引用完整性规则查询。"""

    manifest: dict[str, Any] = field(default_factory=dict)
    factions: dict[str, dict] = field(default_factory=dict)
    chassis: dict[str, dict] = field(default_factory=dict)
    chassis_file: dict[str, str] = field(default_factory=dict)
    forms: dict[str, dict] = field(default_factory=dict)
    form_owner: dict[str, str] = field(default_factory=dict)
    form_file: dict[str, str] = field(default_factory=dict)
    weapons: dict[str, dict] = field(default_factory=dict)
    abilities: dict[str, dict] = field(default_factory=dict)
    overlays: dict[str, dict] = field(default_factory=dict)
    pilots: dict[str, dict] = field(default_factory=dict)
    traits: dict[str, dict] = field(default_factory=dict)
    locales: dict[str, dict] = field(default_factory=dict)
    base_locale: str | None = None


# --------------------------------------------------------------------------
# YAML 载入（禁止重复键，避免静默覆盖）
# --------------------------------------------------------------------------


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                None, None, f"重复的键 {key!r}", key_node.start_mark
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


# --------------------------------------------------------------------------
# 内置 JSON Schema 子集校验器（jsonschema 缺失时使用）
# --------------------------------------------------------------------------

_TYPES: dict[str, Any] = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    py_type = _TYPES.get(expected)
    if py_type is None:
        return True
    if py_type is not bool and isinstance(value, bool):
        return False
    return isinstance(value, py_type)


def _resolve_ref(ref: str, root: dict) -> dict:
    if not ref.startswith("#"):
        raise ValueError(f"内置校验器仅支持文档内 $ref，收到 {ref!r}")
    node: Any = root
    for token in ref.lstrip("#/").split("/"):
        if not token:
            continue
        node = node[token.replace("~1", "/").replace("~0", "~")]
    return node


def _mini_validate(value: Any, schema: dict, root: dict, path: str) -> Iterator[str]:
    if "$ref" in schema:
        yield from _mini_validate(value, _resolve_ref(schema["$ref"], root), root, path)
        return

    if "type" in schema:
        expected = schema["type"]
        options = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, option) for option in options):
            yield f"{path}: 类型应为 {expected}，实际为 {type(value).__name__}"
            return

    if "enum" in schema and value not in schema["enum"]:
        yield f"{path}: {value!r} 不在允许值 {schema['enum']} 内"
    if "const" in schema and value != schema["const"]:
        yield f"{path}: 应为常量 {schema['const']!r}"

    for combiner in ("allOf",):
        for sub in schema.get(combiner, []):
            yield from _mini_validate(value, sub, root, path)
    for combiner in ("anyOf", "oneOf"):
        subs = schema.get(combiner)
        if subs and not any(
            not list(_mini_validate(value, sub, root, path)) for sub in subs
        ):
            yield f"{path}: 不满足 {combiner} 中的任何分支"

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            yield f"{path}: {value!r} 不匹配 pattern {pattern}"
        if "minLength" in schema and len(value) < schema["minLength"]:
            yield f"{path}: 长度小于 {schema['minLength']}"

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            yield f"{path}: {value} 小于最小值 {schema['minimum']}"
        if "maximum" in schema and value > schema["maximum"]:
            yield f"{path}: {value} 大于最大值 {schema['maximum']}"

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            yield f"{path}: 元素数量少于 {schema['minItems']}"
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            yield f"{path}: 元素数量多于 {schema['maxItems']}"
        if schema.get("uniqueItems"):
            seen: list[Any] = []
            for item in value:
                if item in seen:
                    yield f"{path}: 存在重复元素 {item!r}"
                    break
                seen.append(item)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                yield from _mini_validate(item, item_schema, root, f"{path}[{index}]")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                yield f"{path}: 缺少必填字段 {key!r}"
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            yield f"{path}: 字段数量少于 {schema['minProperties']}"
        properties = schema.get("properties", {})
        pattern_properties = schema.get("patternProperties", {})
        additional = schema.get("additionalProperties", True)
        for key, sub_value in value.items():
            child = f"{path}.{key}" if path else str(key)
            matched = False
            if key in properties:
                matched = True
                yield from _mini_validate(sub_value, properties[key], root, child)
            for pattern, sub_schema in pattern_properties.items():
                if re.search(pattern, str(key)):
                    matched = True
                    yield from _mini_validate(sub_value, sub_schema, root, child)
            if not matched:
                if additional is False:
                    yield f"{path}: 不允许的字段 {key!r}"
                elif isinstance(additional, dict):
                    yield from _mini_validate(sub_value, additional, root, child)


def schema_errors(instance: Any, schema: dict) -> list[str]:
    if jsonschema is not None:
        validator = jsonschema.Draft202012Validator(schema)
        messages = []
        for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
            location = "$" + "".join(
                f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.path
            )
            messages.append(f"{location}: {error.message}")
        return messages
    return list(_mini_validate(instance, schema, schema, "$"))


# --------------------------------------------------------------------------
# 校验主体
# --------------------------------------------------------------------------


class DataValidator:
    SCHEMA_BY_KIND = {
        "manifest": "units_manifest.schema.json",
        "chassis": "chassis.schema.json",
        "form_set": "form_set.schema.json",
        "weapon_library": "weapon_library.schema.json",
        "ability_library": "ability_library.schema.json",
        "overlay_library": "overlay_library.schema.json",
        "pilot_library": "pilot_library.schema.json",
        "locale": "locale.schema.json",
    }

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.schema_dir = data_dir / "schema"
        self.issues: list[Issue] = []
        self.documents: list[Document] = []
        self.registry = Registry()
        self._schemas: dict[str, dict] = {}
        self._referenced_files: set[str] = set()

    # -- 基础设施 ---------------------------------------------------------

    def add(self, level: str, rule: str, location: str, message: str) -> None:
        self.issues.append(Issue(level, rule, location, message))

    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.level == ERROR)

    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.level == WARNING)

    def load_schema(self, name: str) -> dict | None:
        if name not in self._schemas:
            path = self.schema_dir / name
            if not path.is_file():
                self.add(ERROR, "R-SCHEMA-000", f"schema/{name}", "Schema 文件不存在")
                return None
            self._schemas[name] = json.loads(path.read_text(encoding="utf-8"))
        return self._schemas[name]

    def load_yaml(self, rel_path: str) -> Any | None:
        path = self.data_dir / rel_path
        if not path.is_file():
            self.add(ERROR, "R-MANIFEST-001", rel_path, "引用的数据文件不存在")
            return None
        try:
            return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        except yaml.YAMLError as exc:
            self.add(ERROR, "R-SCHEMA-000", rel_path, f"YAML 解析失败：{exc}")
            return None

    def load_document(self, kind: str, rel_path: str) -> Document | None:
        self._referenced_files.add(rel_path)
        data = self.load_yaml(rel_path)
        if data is None:
            return None
        schema = self.load_schema(self.SCHEMA_BY_KIND[kind])
        if schema is not None:
            for message in schema_errors(data, schema):
                self.add(ERROR, "R-SCHEMA-000", rel_path, message)
        document = Document(kind, rel_path, data)
        self.documents.append(document)
        return document

    # -- 载入 -------------------------------------------------------------

    def load_all(self) -> None:
        manifest_doc = self.load_document("manifest", "units_manifest.yaml")
        if manifest_doc is None:
            return
        manifest = manifest_doc.data
        if not isinstance(manifest, dict):
            return
        self.registry.manifest = manifest

        for faction in manifest.get("factions", []) or []:
            self._register(self.registry.factions, faction, "units_manifest.yaml", "faction")

        libraries = manifest.get("libraries", {}) or {}
        for rel_path in libraries.get("weapons", []) or []:
            doc = self.load_document("weapon_library", rel_path)
            if doc:
                for weapon in doc.data.get("weapons", []) or []:
                    self._register(self.registry.weapons, weapon, rel_path, "weapon")
        for rel_path in libraries.get("abilities", []) or []:
            doc = self.load_document("ability_library", rel_path)
            if doc:
                for ability in doc.data.get("abilities", []) or []:
                    self._register(self.registry.abilities, ability, rel_path, "ability")
        for rel_path in libraries.get("overlays", []) or []:
            doc = self.load_document("overlay_library", rel_path)
            if doc:
                for overlay in doc.data.get("overlays", []) or []:
                    self._register(self.registry.overlays, overlay, rel_path, "overlay")
        for rel_path in libraries.get("pilots", []) or []:
            doc = self.load_document("pilot_library", rel_path)
            if doc:
                for trait in doc.data.get("traits", []) or []:
                    self._register(self.registry.traits, trait, rel_path, "trait")
                for pilot in doc.data.get("pilots", []) or []:
                    self._register(self.registry.pilots, pilot, rel_path, "pilot")
        for rel_path in libraries.get("locales", []) or []:
            doc = self.load_document("locale", rel_path)
            if doc:
                locale = doc.data.get("locale")
                self.registry.locales[locale] = doc.data
                if doc.data.get("base"):
                    if self.registry.base_locale and self.registry.base_locale != locale:
                        self.add(
                            ERROR,
                            "R-LOC-009",
                            rel_path,
                            f"存在多个 base 语言：{self.registry.base_locale} 与 {locale}",
                        )
                    self.registry.base_locale = locale

        for entry in manifest.get("chassis_index", []) or []:
            rel_path = entry.get("ref") if isinstance(entry, dict) else None
            if not rel_path:
                continue
            doc = self.load_document("chassis", rel_path)
            if not doc or not isinstance(doc.data, dict):
                continue
            chassis_id = doc.data.get("id")
            if isinstance(chassis_id, str):
                self._register(self.registry.chassis, doc.data, rel_path, "chassis")
                self.registry.chassis_file[chassis_id] = rel_path
            forms_ref = doc.data.get("forms_ref")
            if isinstance(forms_ref, str):
                self._load_form_set(forms_ref)

    def _load_form_set(self, rel_path: str) -> None:
        if rel_path in self._referenced_files:
            self.add(ERROR, "R-CHASSIS-001", rel_path, "同一形态文件被多个底盘引用")
            return
        doc = self.load_document("form_set", rel_path)
        if not doc or not isinstance(doc.data, dict):
            return
        owner = doc.data.get("parent_chassis")
        for form in doc.data.get("forms", []) or []:
            if not isinstance(form, dict):
                continue
            form_id = form.get("id")
            if not isinstance(form_id, str):
                continue
            self._register(self.registry.forms, form, rel_path, "form")
            self.registry.form_file[form_id] = rel_path
            if form_id in self.registry.form_owner:
                self.add(
                    ERROR,
                    "R-CHASSIS-001",
                    rel_path,
                    f"形态 {form_id} 归属于多个底盘",
                )
            elif isinstance(owner, str):
                self.registry.form_owner[form_id] = owner

    def _register(self, table: dict, entry: Any, rel_path: str, label: str) -> None:
        if not isinstance(entry, dict):
            return
        entry_id = entry.get("id")
        if not isinstance(entry_id, str):
            return
        if entry_id in table:
            self.add(ERROR, "R-ID-001", rel_path, f"{label} ID 重复：{entry_id}")
            return
        table[entry_id] = entry

    # -- 引用完整性规则 ----------------------------------------------------

    def check_references(self) -> None:
        self._check_orphan_files()
        self._check_chassis()
        self._check_forms()
        self._check_pilots()
        self._check_locales()
        self._check_balance()
        self._check_milestone()

    def _check_orphan_files(self) -> None:
        for path in sorted(self.data_dir.rglob("*.yaml")):
            rel_path = path.relative_to(self.data_dir).as_posix()
            if rel_path.startswith("schema/"):
                continue
            if rel_path not in self._referenced_files:
                self.add(
                    ERROR,
                    "R-MANIFEST-002",
                    rel_path,
                    "文件未被 units_manifest.yaml 引用（孤儿数据不会进入构建产物）",
                )

    def _check_chassis(self) -> None:
        registry = self.registry
        for chassis_id, chassis in sorted(registry.chassis.items()):
            location = registry.chassis_file.get(chassis_id, chassis_id)
            declared = list(chassis.get("forms", []) or [])
            owned = sorted(
                form_id
                for form_id, owner in registry.form_owner.items()
                if owner == chassis_id
            )
            for form_id in declared:
                if form_id not in registry.forms:
                    self.add(
                        ERROR, "R-CHASSIS-001", location, f"声明的形态不存在：{form_id}"
                    )
                elif registry.form_owner.get(form_id) != chassis_id:
                    self.add(
                        ERROR,
                        "R-CHASSIS-001",
                        location,
                        f"形态 {form_id} 的 parent_chassis 与本底盘不一致",
                    )
            for form_id in owned:
                if form_id not in declared:
                    self.add(
                        ERROR,
                        "R-CHASSIS-001",
                        registry.form_file.get(form_id, location),
                        f"形态 {form_id} 未在底盘 {chassis_id} 的 forms 列表中声明",
                    )

            default_form = chassis.get("default_form")
            if default_form not in declared:
                self.add(
                    ERROR,
                    "R-CHASSIS-002",
                    location,
                    f"default_form {default_form} 不在 forms 列表中",
                )

            policy_type = (chassis.get("form_switch_policy") or {}).get("type", "none")
            if len(declared) > 1 and policy_type == "none":
                self.add(
                    ERROR,
                    "R-CHASSIS-003",
                    location,
                    "多形态底盘必须声明 form_switch_policy（换装或变形策略）",
                )
            if len(declared) == 1 and policy_type != "none":
                self.add(
                    WARNING,
                    "R-CHASSIS-003",
                    location,
                    f"单形态底盘声明了 form_switch_policy.type={policy_type}",
                )

            for faction_field in ("faction_production", "faction_playable"):
                faction_id = chassis.get(faction_field)
                if faction_id and faction_id not in registry.factions:
                    self.add(
                        ERROR,
                        "R-FACTION-008",
                        location,
                        f"{faction_field} 未在 manifest.factions 中定义：{faction_id}",
                    )

            self._check_asset_binding(chassis, location, chassis_id)

    def _check_forms(self) -> None:
        registry = self.registry
        for form_id, form in sorted(registry.forms.items()):
            location = registry.form_file.get(form_id, form_id)
            owner = registry.form_owner.get(form_id)

            slots_seen: set[tuple[str, str]] = set()
            has_attack = False
            for entry in form.get("weapons", []) or []:
                slot = entry.get("slot")
                weapon_id = entry.get("weapon_id")
                if (slot, weapon_id) in slots_seen:
                    self.add(
                        ERROR,
                        "R-FORM-012",
                        location,
                        f"{form_id}: 重复的槽位/武装组合 {slot}/{weapon_id}",
                    )
                slots_seen.add((slot, weapon_id))
                weapon = registry.weapons.get(weapon_id)
                if weapon is None:
                    self.add(
                        ERROR,
                        "R-WEAPON-003",
                        location,
                        f"{form_id}: 武装不存在 {weapon_id}",
                    )
                    continue
                if slot not in (weapon.get("slot_types") or []):
                    self.add(
                        ERROR,
                        "R-WEAPON-004",
                        location,
                        f"{form_id}: 武装 {weapon_id} 不支持槽位 {slot}"
                        f"（允许 {weapon.get('slot_types')}）",
                    )
                if slot in ("main", "melee"):
                    has_attack = True
            if not has_attack:
                self.add(
                    ERROR,
                    "R-FORM-005",
                    location,
                    f"{form_id}: 形态必须至少装备 1 件 main 或 melee 武装",
                )

            for ability_id in form.get("abilities", []) or []:
                if ability_id not in registry.abilities:
                    self.add(
                        ERROR,
                        "R-ABILITY-006",
                        location,
                        f"{form_id}: 技能不存在 {ability_id}",
                    )

            for overlay_entry in form.get("mode_overlays", []) or []:
                overlay_id = overlay_entry.get("overlay_id")
                overlay = registry.overlays.get(overlay_id)
                if overlay is None:
                    self.add(
                        ERROR,
                        "R-OVERLAY-007",
                        location,
                        f"{form_id}: 叠加层不存在 {overlay_id}",
                    )
                    continue
                required_trait = overlay.get("requires_trait")
                declared_trait = (overlay_entry.get("requires") or {}).get("pilot_trait")
                for trait_id in filter(None, {required_trait, declared_trait}):
                    if trait_id not in registry.traits:
                        self.add(
                            ERROR,
                            "R-OVERLAY-007",
                            location,
                            f"{form_id}: 特质不存在 {trait_id}",
                        )
                if required_trait and declared_trait != required_trait:
                    self.add(
                        WARNING,
                        "R-OVERLAY-007",
                        location,
                        f"{form_id}: 叠加层 {overlay_id} 要求特质 {required_trait}，"
                        "但形态未在 requires.pilot_trait 中显式声明",
                    )

            for edge in form.get("transform_graph", []) or []:
                target_id = edge.get("to")
                target = registry.forms.get(target_id)
                if target is None:
                    self.add(
                        ERROR,
                        "R-FORM-002",
                        location,
                        f"{form_id}: 变形目标不存在 {target_id}",
                    )
                    continue
                if registry.form_owner.get(target_id) != owner:
                    self.add(
                        ERROR,
                        "R-FORM-002",
                        location,
                        f"{form_id}: 变形目标 {target_id} 属于其他底盘",
                    )
                    continue
                if edge.get("one_way"):
                    continue
                back_edges = [
                    back.get("to") for back in target.get("transform_graph", []) or []
                ]
                if form_id not in back_edges:
                    self.add(
                        ERROR,
                        "R-FORM-002",
                        location,
                        f"{form_id} → {target_id}: 双向变形边未闭合"
                        "（如为单程请显式声明 one_way: true）",
                    )

            self._check_asset_binding(form, location, form_id)

    def _check_pilots(self) -> None:
        registry = self.registry
        for chassis_id, chassis in sorted(registry.chassis.items()):
            location = registry.chassis_file.get(chassis_id, chassis_id)
            pilots = chassis.get("compatible_pilots") or []
            if not pilots:
                self.add(
                    WARNING,
                    "R-PILOT-004",
                    location,
                    f"{chassis_id}: compatible_pilots 为空，视为剧情专用不可选机体",
                )
            for pilot_id in pilots:
                if pilot_id not in registry.pilots:
                    self.add(
                        ERROR,
                        "R-PILOT-004",
                        location,
                        f"{chassis_id}: 驾驶员不存在 {pilot_id}",
                    )
        for pilot_id, pilot in sorted(registry.pilots.items()):
            for trait_id in pilot.get("traits") or []:
                if trait_id not in registry.traits:
                    self.add(
                        ERROR, "R-PILOT-004", "pilots", f"{pilot_id}: 特质不存在 {trait_id}"
                    )
            for ability_id in pilot.get("abilities") or []:
                if ability_id not in registry.abilities:
                    self.add(
                        ERROR,
                        "R-ABILITY-006",
                        "pilots",
                        f"{pilot_id}: 技能不存在 {ability_id}",
                    )

    def _check_locales(self) -> None:
        registry = self.registry
        used: dict[str, str] = {}
        for document in self.documents:
            if document.kind == "locale":
                continue
            for key in _collect_loc_keys(document.data):
                used.setdefault(key, document.rel_path)

        if registry.base_locale is None:
            self.add(ERROR, "R-LOC-009", "locales", "缺少 base: true 的基准语言文件")
            return

        for locale, document in sorted(registry.locales.items()):
            entries = document.get("entries", {}) or {}
            is_base = locale == registry.base_locale
            for key, source in sorted(used.items()):
                if key not in entries:
                    self.add(
                        ERROR if is_base else WARNING,
                        "R-LOC-009",
                        f"locales/{locale}",
                        f"缺少本地化条目 {key}（引用自 {source}）",
                    )
            if is_base:
                for key in sorted(set(entries) - set(used)):
                    self.add(
                        INFO,
                        "R-LOC-010",
                        f"locales/{locale}",
                        f"未被任何数据引用的条目 {key}",
                    )

    def _check_balance(self) -> None:
        low = POWER_BUDGET_BASELINE * (1 - POWER_BUDGET_TOLERANCE)
        high = POWER_BUDGET_BASELINE * (1 + POWER_BUDGET_TOLERANCE)
        for chassis_id, chassis in sorted(self.registry.chassis.items()):
            budget = chassis.get("power_budget")
            if not isinstance(budget, int):
                continue
            if not low <= budget <= high:
                self.add(
                    WARNING,
                    "R-BALANCE-006",
                    self.registry.chassis_file.get(chassis_id, chassis_id),
                    f"{chassis_id}: power_budget {budget} 偏离基准 "
                    f"{POWER_BUDGET_BASELINE} 超过 ±{int(POWER_BUDGET_TOLERANCE * 100)}%",
                )

    def _check_milestone(self) -> None:
        milestone = self.registry.manifest.get("milestone")
        count = len(self.registry.chassis)
        if milestone == "M0" and count != M0_EXPECTED_CHASSIS:
            self.add(
                WARNING,
                "R-MILESTONE-011",
                "units_manifest.yaml",
                f"M0 首发名单要求 {M0_EXPECTED_CHASSIS} 台底盘，当前 {count} 台",
            )

    def _check_asset_binding(self, entry: dict, location: str, entry_id: str) -> None:
        binding = entry.get("asset_binding")
        if not isinstance(binding, dict):
            self.add(
                WARNING, "R-ASSET-005", location, f"{entry_id}: 缺少 asset_binding（开发中条目）"
            )
            return
        if binding.get("placeholder") is not True:
            self.add(
                ERROR,
                "R-ASSET-010",
                location,
                f"{entry_id}: M0 禁止非占位资产，asset_binding.placeholder 必须为 true",
            )

    # -- 构建产物 ---------------------------------------------------------

    def build_index(self) -> dict:
        registry = self.registry
        base_entries = {}
        if registry.base_locale:
            base_entries = registry.locales[registry.base_locale].get("entries", {}) or {}

        def name_of(key: str | None) -> str:
            return base_entries.get(key, key or "")

        chassis_entries = []
        for chassis_id, chassis in sorted(registry.chassis.items()):
            forms = []
            for form_id in chassis.get("forms", []) or []:
                form = registry.forms.get(form_id, {})
                forms.append(
                    {
                        "id": form_id,
                        "display_name": name_of(form.get("display_name_key")),
                        "type": form.get("type"),
                        "weapons": [
                            {
                                "slot": weapon.get("slot"),
                                "id": weapon.get("weapon_id"),
                                "display_name": name_of(
                                    (registry.weapons.get(weapon.get("weapon_id")) or {}).get(
                                        "display_name_key"
                                    )
                                ),
                            }
                            for weapon in form.get("weapons", []) or []
                        ],
                        "abilities": list(form.get("abilities", []) or []),
                        "mode_overlays": [
                            overlay.get("overlay_id")
                            for overlay in form.get("mode_overlays", []) or []
                        ],
                        "transform_targets": [
                            edge.get("to") for edge in form.get("transform_graph", []) or []
                        ],
                    }
                )
            chassis_entries.append(
                {
                    "id": chassis_id,
                    "model_number": chassis.get("model_number"),
                    "display_name": name_of(chassis.get("display_name_key")),
                    "description": name_of(chassis.get("description_key")),
                    "series": chassis.get("series"),
                    "era": chassis.get("era"),
                    "faction_production": chassis.get("faction_production"),
                    "faction_playable": chassis.get("faction_playable"),
                    "tags": list(chassis.get("tags", []) or []),
                    "power_budget": chassis.get("power_budget"),
                    "base_stats": chassis.get("base_stats", {}),
                    "default_form": chassis.get("default_form"),
                    "forms": forms,
                }
            )

        return {
            "_generated_by": "tools/data_validator/validate.py",
            "_warning": "构建产物，请勿手工编辑；由 make validate-data 重新生成。",
            "schema_version": registry.manifest.get("schema_version"),
            "balance_patch": registry.manifest.get("balance_patch"),
            "milestone": registry.manifest.get("milestone"),
            "locale": registry.base_locale,
            "counts": {
                "chassis": len(registry.chassis),
                "forms": len(registry.forms),
                "weapons": len(registry.weapons),
                "abilities": len(registry.abilities),
                "overlays": len(registry.overlays),
                "pilots": len(registry.pilots),
            },
            "factions": [
                {"id": faction_id, "display_name": name_of(faction.get("name_key"))}
                for faction_id, faction in sorted(registry.factions.items())
            ],
            "chassis": chassis_entries,
        }


def _collect_loc_keys(node: Any) -> Iterator[str]:
    if isinstance(node, str):
        if node.startswith("loc."):
            yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _collect_loc_keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _collect_loc_keys(value)


# --------------------------------------------------------------------------
# 输出
# --------------------------------------------------------------------------

_LEVEL_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}


def render_text(issues: Iterable[Issue]) -> str:
    labels = {ERROR: "ERROR  ", WARNING: "WARNING", INFO: "INFO   "}
    return "\n".join(
        f"{labels[issue.level]} [{issue.rule}] {issue.location}: {issue.message}"
        for issue in issues
    )


def render_github(issues: Iterable[Issue]) -> str:
    commands = {ERROR: "error", WARNING: "warning", INFO: "notice"}
    lines = []
    for issue in issues:
        message = f"[{issue.rule}] {issue.location}: {issue.message}".replace("\n", " ")
        lines.append(f"::{commands[issue.level]} title={issue.rule}::{message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate.py", description="校验 data/ 下的机体与武装数据"
    )
    parser.add_argument(
        "--data-dir", type=Path, default=REPO_ROOT / "data", help="数据目录（默认 data/）"
    )
    parser.add_argument(
        "--strict", action="store_true", help="将 Warning 也视为失败"
    )
    parser.add_argument(
        "--format", choices=("text", "github"), default="text", help="输出格式"
    )
    parser.add_argument(
        "--emit-index", type=Path, help="校验通过后写出构建产物 JSON（供 Godot 载入）"
    )
    parser.add_argument(
        "--check-index",
        type=Path,
        help="校验构建产物是否与当前数据一致（CI 用，不写文件）",
    )
    parser.add_argument("--quiet", action="store_true", help="仅输出结论行")
    args = parser.parse_args(argv)

    data_dir: Path = args.data_dir
    if not data_dir.is_dir():
        sys.stderr.write(f"数据目录不存在：{data_dir}\n")
        return 2

    validator = DataValidator(data_dir)
    validator.load_all()
    validator.check_references()

    issues = sorted(
        validator.issues, key=lambda i: (_LEVEL_ORDER[i.level], i.rule, i.location, i.message)
    )
    if issues and not args.quiet:
        renderer = render_github if args.format == "github" else render_text
        print(renderer(issues))
        print()

    errors = validator.error_count()
    warnings = validator.warning_count()
    engine = "jsonschema" if jsonschema is not None else "内置子集校验器"
    print(
        f"已校验 {len(validator.documents)} 个文件 / "
        f"{len(validator.registry.chassis)} 台底盘 / "
        f"{len(validator.registry.forms)} 个形态 / "
        f"{len(validator.registry.weapons)} 件武装"
        f"（Schema 引擎：{engine}）"
    )
    print(f"结果：{errors} error, {warnings} warning")

    failed = errors > 0 or (args.strict and warnings > 0)

    if args.check_index or args.emit_index:
        index = validator.build_index()
        payload = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
        if args.check_index:
            target: Path = args.check_index
            if not target.is_file():
                print(f"构建产物缺失：{target}（运行 make validate-data 生成）")
                failed = True
            elif target.read_text(encoding="utf-8") != payload:
                print(f"构建产物已过期：{target}（运行 make validate-data 重新生成）")
                failed = True
            else:
                print(f"构建产物是最新的：{target}")
        if args.emit_index and not failed:
            target = args.emit_index
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding="utf-8")
            print(f"已写出构建产物：{target}")

    if failed:
        print("校验失败。")
        return 1
    print("校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
