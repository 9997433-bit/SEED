#!/usr/bin/env python3
"""检查 Godot headless 运行日志：放行 headless 假渲染器的已知噪声，其余错误一律失败。

用法：

    python3 tools/ci/godot_log_filter.py run.log
    python3 tools/ci/godot_log_filter.py smoke.log --require "SMOKE: OK"

背景：`--headless` 下 Godot 使用 dummy RenderingServer，场景里的 Mesh 资源在
服务端不存在，`mesh_get_surface_count` 之类的调用会刷出 `Parameter "m" is null.`。
这类噪声在无头环境里无法避免，也不代表工程有问题，所以按「错误发生位置在
servers/rendering/dummy/ 下」放行；SCRIPT ERROR、资源载入失败等一律视为构建失败。

退出码：0 通过；1 发现未放行的错误或缺少 --require 标记。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# 一条 Godot 诊断记录的首行，例如 "ERROR: Parameter \"m\" is null."
HEADER_RE = re.compile(r"^(?P<severity>SCRIPT ERROR|USER ERROR|ERROR|USER WARNING|WARNING):\s?(?P<message>.*)$")
# 紧随其后的位置行，例如 "   at: mesh_get_surface_count (servers/rendering/dummy/...:120)"
AT_RE = re.compile(r"^\s+at:\s*(?P<location>.*)$")

FAILING_SEVERITIES = {"ERROR", "USER ERROR", "SCRIPT ERROR"}

# (消息正则, 位置正则)；两者都匹配才放行。位置为空时用 "" 参与匹配。
ALLOWED_RULES: list[tuple[str, str]] = [
    # headless 假渲染器：网格/材质在服务端不存在
    (r".*", r"servers/rendering/dummy/"),
    # headless 无音频设备时的驱动回退
    (r"Cannot initialize audio driver\. Trying with the Dummy driver\.", r".*"),
]

COMPILED_RULES = [(re.compile(m), re.compile(loc)) for m, loc in ALLOWED_RULES]


@dataclass
class Diagnostic:
    severity: str
    message: str
    line_no: int
    locations: list[str] = field(default_factory=list)

    @property
    def location(self) -> str:
        return self.locations[0] if self.locations else ""

    def is_allowed(self) -> bool:
        return any(
            msg_re.search(self.message) and loc_re.search(self.location)
            for msg_re, loc_re in COMPILED_RULES
        )

    def render(self) -> str:
        suffix = f"  @ {self.location}" if self.location else ""
        return f"  L{self.line_no}: {self.severity}: {self.message}{suffix}"


def parse(text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    current: Diagnostic | None = None
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        at_match = AT_RE.match(line)
        if at_match and current is not None:
            current.locations.append(at_match.group("location"))
            continue
        header = HEADER_RE.match(line)
        if header:
            current = Diagnostic(
                severity=header.group("severity"),
                message=header.group("message").strip(),
                line_no=line_no,
            )
            diagnostics.append(current)
            continue
        current = None
    return diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log", type=Path, help="Godot headless 运行日志（stdout + stderr 合并）")
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="TEXT",
        help="日志中必须出现的标记，可重复指定",
    )
    parser.add_argument("--quiet", action="store_true", help="通过时不打印摘要")
    args = parser.parse_args(argv)

    if not args.log.is_file():
        print(f"::error::日志文件不存在：{args.log}", file=sys.stderr)
        return 1

    text = args.log.read_text(encoding="utf-8", errors="replace")
    diagnostics = parse(text)

    failures = [d for d in diagnostics if d.severity in FAILING_SEVERITIES and not d.is_allowed()]
    allowed = [d for d in diagnostics if d.severity in FAILING_SEVERITIES and d.is_allowed()]
    warnings = [d for d in diagnostics if d.severity not in FAILING_SEVERITIES]

    missing = [marker for marker in args.require if marker not in text]

    for marker in missing:
        print(f"::error::日志中缺少必需标记：{marker}", file=sys.stderr)

    if failures:
        print(f"::error::Godot 日志中有 {len(failures)} 条未放行的错误：", file=sys.stderr)
        for diagnostic in failures:
            print(diagnostic.render(), file=sys.stderr)

    if failures or missing:
        return 1

    if not args.quiet:
        print(
            f"Godot 日志检查通过：放行 headless 噪声 {len(allowed)} 条，"
            f"警告 {len(warnings)} 条，未放行错误 0 条。"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
