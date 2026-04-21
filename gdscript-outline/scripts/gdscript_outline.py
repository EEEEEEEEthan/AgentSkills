#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 .gd 文件提取大纲（父类、class_name、字段/属性/方法），无需完整 AST。"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


def _leading_indent_level(line: str) -> int:
    """GDScript 常用：一级缩进 = 一个 tab 或 4 空格。"""
    i = 0
    level = 0
    while i < len(line):
        if line[i] == "\t":
            level += 1
            i += 1
        elif line[i] == " ":
            j = i
            while j < len(line) and line[j] == " ":
                j += 1
            level += (j - i) // 4
            i = j
        else:
            break
    return level


def _strip_trailing_comment(line: str) -> str:
    """去掉行尾 # 注释（忽略字符串内的 #）。"""
    out: list[str] = []
    i = 0
    in_str = False
    quote = ""
    escape = False
    while i < len(line):
        c = line[i]
        if not in_str:
            if c in "\"'":
                in_str = True
                quote = c
                out.append(c)
            elif c == "#":
                break
            else:
                out.append(c)
        else:
            out.append(c)
            if escape:
                escape = False
            elif c == "\\" and quote == '"':
                escape = True
            elif c == quote:
                in_str = False
                quote = ""
        i += 1
    return "".join(out).rstrip()


_RE_EXTENDS = re.compile(
    r"^(?:@[\w.]+\s+)*extends\s+([\w.]+)(?:\s+as\s+\w+)?\s*(?:#.*)?$"
)
_RE_CLASS_NAME = re.compile(r"^(?:@[\w.]+\s+)*class_name\s+(\w+)\s*(?:#.*)?$")
_RE_SIGNAL = re.compile(r"^signal\s+(\w+)\b")
_RE_CONST = re.compile(r"^(?:@[\w.]+\s+)*(static\s+)?const\s+(\w+)")
_RE_VAR_HEAD = re.compile(
    r"^(?:(@onready|@export|@export_category|@export_group|@export_subgroup)\s+)?(static\s+)?var\s+(\w+)\b"
)
_RE_FUNC = re.compile(r"^(?:@[\w.]+\s+)*(static\s+)?func\s+(\w+)\s*\(")


def _scan_type_expression(s: str, start: int) -> tuple[str | None, int]:
    """从 start 起扫描一段 GD 类型（含 `[]` 嵌套），返回 (类型文本, 结束下标)。"""
    n = len(s)
    i = start
    while i < n and s[i] in " \t":
        i += 1
    if i >= n:
        return None, start
    depth = 0
    t0 = i
    while i < n:
        c = s[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        elif depth == 0:
            if c in "=:":
                break
        i += 1
    t = s[t0:i].strip()
    return (t if t else None), i


def _extract_var_or_const_type(rest_after_name: str) -> str | None:
    """解析 var/const 名称之后的显式类型（`: Type`），无则返回 None。"""
    rest = rest_after_name.lstrip()
    if rest.startswith(":="):
        return None
    if not rest.startswith(":"):
        return None
    typ, _ = _scan_type_expression(rest, 1)
    return typ


def _extract_func_return_type(func_line: str) -> str | None:
    """解析 `func ... ) -> Type` 的返回类型。"""
    m = re.search(r"\)\s*->\s*", func_line)
    if not m:
        return None
    typ, _ = _scan_type_expression(func_line, m.end())
    return typ


def _inner_of_matching_paren(s: str, open_idx: int) -> str:
    """open_idx 指向 `(`，返回成对括号内原文（不含括号）。"""
    if open_idx < 0 or open_idx >= len(s) or s[open_idx] != "(":
        return ""
    depth = 1
    i = open_idx + 1
    while i < len(s):
        c = s[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return s[open_idx + 1 : i]
        i += 1
    return ""


def _format_method_line(s: str, m: re.Match[str]) -> str:
    """含参数列表与 `->` 返回类型（若有）。"""
    is_static = bool(m.group(1))
    fname = m.group(2)
    prefix = "static " if is_static else ""
    open_idx = m.end() - 1
    if open_idx < 0 or open_idx >= len(s) or s[open_idx] != "(":
        open_idx = s.find("(", m.start())
    params = _inner_of_matching_paren(s, open_idx) if open_idx >= 0 else ""
    mid = f"({params.strip()})" if params.strip() else "()"
    ret = _extract_func_return_type(s)
    if ret:
        return f"{prefix}func {fname}{mid} -> {ret}"
    return f"{prefix}func {fname}{mid}"


def _format_signal_line(s: str) -> str:
    """`signal name` 或带 `(args)` 整段（含类型）。"""
    s = s.strip()
    m = re.match(r"^signal\s+(\w+)", s)
    if not m:
        return s
    name = m.group(1)
    tail = s[m.end() :].lstrip()
    if tail.startswith("("):
        depth = 0
        for j, c in enumerate(tail):
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return f"signal {name}{tail[: j + 1]}"
        return f"signal {name}{tail}"
    return f"signal {name}"


def _with_type(base: str, typ: str | None) -> str:
    return f"{base}: {typ}" if typ else base


def _parse_gd_outline(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    parent: str | None = None
    class_name: str | None = None
    fields: list[str] = []
    properties: list[str] = []
    methods: list[str] = []
    signals: list[str] = []

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("#"):
            i += 1
            continue

        line = _strip_trailing_comment(raw)
        if not line.strip():
            i += 1
            continue

        if _leading_indent_level(line) != 0:
            i += 1
            continue

        s = line.strip()

        m_ext = _RE_EXTENDS.match(s)
        if m_ext:
            parent = m_ext.group(1)
            i += 1
            continue

        m_cn = _RE_CLASS_NAME.match(s)
        if m_cn:
            class_name = m_cn.group(1)
            i += 1
            continue

        m_sig = _RE_SIGNAL.match(s)
        if m_sig:
            signals.append(_format_signal_line(s))
            i += 1
            continue

        m_co = _RE_CONST.match(s)
        if m_co:
            st, cname = m_co.group(1), m_co.group(2)
            rest = s[m_co.end() :].lstrip()
            typ = _extract_var_or_const_type(rest)
            base = f"static const {cname}" if st else f"const {cname}"
            fields.append(_with_type(base, typ))
            i += 1
            continue

        m_va = _RE_VAR_HEAD.match(s)
        if m_va:
            deco = m_va.group(1) or ""
            is_static = bool(m_va.group(2))
            var_name = m_va.group(3)
            is_export = deco and "export" in deco
            is_onready = deco == "@onready"
            rest = s[m_va.end() :].lstrip()
            typ = _extract_var_or_const_type(rest)
            trailing_colon = rest.rstrip().endswith(":")

            if is_export or is_onready or trailing_colon:
                tag: list[str] = []
                if deco:
                    tag.append(deco)
                if is_static:
                    tag.append("static")
                tag.append(f"var {var_name}")
                properties.append(_with_type(" ".join(tag), typ))
            else:
                if is_static:
                    fields.append(_with_type(f"static var {var_name}", typ))
                else:
                    fields.append(_with_type(f"var {var_name}", typ))

            if trailing_colon:
                i += 1
                while i < len(lines):
                    nl = lines[i]
                    if _leading_indent_level(nl) == 0 and nl.strip():
                        break
                    i += 1
                continue
            i += 1
            continue

        m_fu = _RE_FUNC.match(s)
        if m_fu:
            methods.append(_format_method_line(s, m_fu))
            if s.rstrip().endswith(":"):
                i += 1
                while i < len(lines):
                    nl = lines[i]
                    if _leading_indent_level(nl) == 0 and nl.strip():
                        break
                    i += 1
                continue
            i += 1
            continue

        i += 1

    # 对外大纲：signal 归入「字段」
    fields_out = list(signals) + fields
    return {
        "parent": parent,
        "class_name": class_name,
        "fields": fields_out,
        "properties": properties,
        "methods": methods,
    }


def _format_text(path: Path, data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"文件: {path}")
    lines.append(f"父类: {data['parent'] or '(无 extends)'}")
    lines.append(f"类名: {data['class_name'] or '(无 class_name)'}")
    lines.append("")
    lines.append("[字段]")
    for x in data["fields"]:
        lines.append(x)
    if not data["fields"]:
        lines.append("(无)")
    lines.append("")
    lines.append("[属性]")
    for x in data["properties"]:
        lines.append(x)
    if not data["properties"]:
        lines.append("(无)")
    lines.append("")
    lines.append("[方法]")
    for x in data["methods"]:
        lines.append(x)
    if not data["methods"]:
        lines.append("(无)")
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="提取 GDScript 文件大纲（轻量扫描，适合先读概要）。")
    p.add_argument("path", type=Path, help=".gd 文件路径")
    args = p.parse_args()

    path: Path = args.path
    if not path.is_file():
        print(f"错误: 不是文件: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"错误: 无法读取: {e}", file=sys.stderr)
        sys.exit(1)

    data = _parse_gd_outline(text)
    print(_format_text(path, data), end="")


if __name__ == "__main__":
    main()
