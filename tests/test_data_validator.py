#!/usr/bin/env python3
"""校验器的反向测试：故意破坏数据副本，断言对应规则被触发。

用法：
    python3 tests/test_data_validator.py
（pytest 亦可直接收集本文件中的 test_* 函数。）
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

_spec = importlib.util.spec_from_file_location(
    "validate", REPO_ROOT / "tools" / "data_validator" / "validate.py"
)
assert _spec and _spec.loader
validate = importlib.util.module_from_spec(_spec)
sys.modules["validate"] = validate  # dataclasses 需要模块已注册才能解析注解
_spec.loader.exec_module(validate)


def run_on(data_dir: Path) -> list:
    validator = validate.DataValidator(data_dir)
    validator.load_all()
    validator.check_references()
    return validator.issues


def rules_for(mutate) -> set[str]:
    """把 data/ 复制到临时目录、应用 mutate、返回触发的规则集合。"""
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        shutil.copytree(DATA_DIR, data_dir)
        mutate(data_dir)
        return {
            issue.rule
            for issue in run_on(data_dir)
            if issue.level in (validate.ERROR, validate.WARNING)
        }


def patch(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{path} 中找不到待替换文本：{old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_clean_dataset_has_no_findings() -> None:
    findings = [
        issue for issue in run_on(DATA_DIR) if issue.level in (validate.ERROR, validate.WARNING)
    ]
    assert not findings, "\n".join(validate.render_text(findings).splitlines())


def test_missing_weapon_reference() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "units/forms/gat-x105.yaml",
            "weapon_id: weapon.beam_rifle_standard",
            "weapon_id: weapon.does_not_exist",
        )
    )
    assert "R-WEAPON-003" in rules


def test_weapon_in_wrong_slot() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "units/forms/gat-x105.yaml",
            "      - slot: sub\n        weapon_id: weapon.head_vulcan",
            "      - slot: main\n        weapon_id: weapon.head_vulcan",
        )
    )
    assert "R-WEAPON-004" in rules


def test_form_owned_by_wrong_chassis() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "units/forms/gat-x105.yaml",
            "parent_chassis: chassis.gat_x105",
            "parent_chassis: chassis.zgmf_600",
        )
    )
    assert "R-CHASSIS-001" in rules


def test_default_form_not_in_forms() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "units/chassis/gat-x105.yaml",
            "default_form: form.gat_x105.aile",
            "default_form: form.gat_x105.ghost",
        )
    )
    assert "R-CHASSIS-002" in rules


def test_unclosed_transform_edge() -> None:
    """删掉 MA→MS 的反向边后，MS→MA 这条非单程边应报未闭合。"""

    def break_edge(d: Path) -> None:
        path = d / "units/forms/gat-x303.yaml"
        head, marker, tail = path.read_text(encoding="utf-8").partition(
            "  - id: form.gat_x303.ma"
        )
        tail = tail.replace(
            "    transform_graph:\n"
            "      - to: form.gat_x303.ms\n"
            "        trigger: manual\n"
            "        duration_sec: 2.5\n"
            "        one_way: false\n"
            "        constraints:\n"
            "          forbid_states: [grappled, downed]\n",
            "    transform_graph: []\n",
            1,
        )
        path.write_text(head + marker + tail, encoding="utf-8")

    assert "R-FORM-002" in rules_for(break_edge)


def test_non_placeholder_asset_is_rejected() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "units/chassis/gat-x105.yaml",
            "  placeholder: true",
            "  placeholder: false",
        )
    )
    assert "R-ASSET-010" in rules


def test_missing_locale_entry() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "locales/zh_cn.yaml", "  loc.unit.strike: 强袭\n", ""
        )
    )
    assert "R-LOC-009" in rules


def test_orphan_file_is_reported() -> None:
    def add_orphan(d: Path) -> None:
        (d / "units/chassis/orphan.yaml").write_text("id: chassis.orphan\n", encoding="utf-8")

    assert "R-MANIFEST-002" in rules_for(add_orphan)


def test_duplicate_id() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "weapons/ballistic.yaml",
            "  - id: weapon.head_vulcan",
            "  - id: weapon.beam_rifle_standard",
        )
    )
    assert "R-ID-001" in rules


def test_schema_violation() -> None:
    rules = rules_for(
        lambda d: patch(
            d / "units/chassis/gat-x105.yaml", "power_budget: 1050", 'power_budget: "很强"'
        )
    )
    assert "R-SCHEMA-000" in rules


def test_missing_referenced_file() -> None:
    def drop_file(d: Path) -> None:
        (d / "units/forms/gat-x105.yaml").unlink()

    assert "R-MANIFEST-001" in rules_for(drop_file)


def main() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failures = 0
    for name, test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
        else:
            print(f"ok   {name}")
    print(f"\n{len(tests) - failures}/{len(tests)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
