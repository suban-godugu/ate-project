"""Minimal YAML loader (stdlib only — no PyYAML dependency)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def load_adapter_configs(path: Path) -> dict[str, Any]:
    """Parse a simple YAML subset sufficient for adapter configuration."""
    text = path.read_text(encoding="utf-8")
    return _parse_yaml_subset(text)


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    raw_lines = text.splitlines()
    lines: list[str | None] = []
    for line in raw_lines:
        if not line.strip() or line.strip().startswith("#"):
            lines.append(None)
        else:
            lines.append(line)

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    key_re = re.compile(r"^(\s*)([A-Za-z0-9_]+):\s*(.*)$")
    list_re = re.compile(r"^(\s*)-\s*(.*)$")

    index = 0
    while index < len(lines):
        line = lines[index]
        if line is None:
            index += 1
            continue

        list_match = list_re.match(line)
        if list_match:
            indent, rest = list_match.groups()
            level = len(indent)
            _pop_to_level(stack, level)

            parent = stack[-1][1]
            if not isinstance(parent, list):
                raise ValueError(f"List item outside list at line: {line}")

            item_key = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", rest)
            if item_key:
                key, value = item_key.groups()
                item: dict[str, Any] = {}
                if value == "":
                    next_line = _next_nonempty(lines, index)
                    if next_line and list_re.match(next_line):
                        item[key] = []
                    else:
                        item[key] = {}
                else:
                    item[key] = _parse_value(value.strip())
                parent.append(item)
                stack.append((level, item))
            else:
                parent.append(_parse_value(rest.strip()))
            index += 1
            continue

        match = key_re.match(line)
        if not match:
            index += 1
            continue

        indent, key, value = match.groups()
        level = len(indent)
        _pop_to_level(stack, level)

        parent = stack[-1][1]
        if not isinstance(parent, dict):
            raise ValueError(f"Mapping key outside mapping at line: {line}")

        if value == "":
            next_line = _next_nonempty(lines, index)
            if next_line and list_re.match(next_line):
                node_list: list[Any] = []
                parent[key] = node_list
                stack.append((level, node_list))
            else:
                node_dict: dict[str, Any] = {}
                parent[key] = node_dict
                stack.append((level, node_dict))
        else:
            parent[key] = _parse_value(value.strip())

        index += 1

    return root


def _pop_to_level(stack: list[tuple[int, Any]], level: int) -> None:
    while stack and stack[-1][0] >= level:
        stack.pop()


def _next_nonempty(lines: list[str | None], index: int) -> str | None:
    for offset in range(index + 1, len(lines)):
        if lines[offset] is not None:
            return lines[offset]
    return None


def _parse_value(value: str) -> Any:
    value = value.strip().strip("'\"").strip()
    if not value:
        return ""
    if value.startswith("{") and value.endswith("}"):
        return _parse_inline_dict(value)
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_value(part.strip()) for part in _split_commas(inner)]
    return _coerce_scalar(value)


def _parse_inline_dict(value: str) -> dict[str, Any]:
    inner = value.strip()[1:-1].strip()
    if not inner:
        return {}
    result: dict[str, Any] = {}
    for part in _split_commas(inner):
        if ":" not in part:
            continue
        key, raw = part.split(":", 1)
        result[key.strip()] = _parse_value(raw.strip())
    return result


def _split_commas(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_quote = False
    quote_char = ""

    for char in value:
        if char in {"'", '"'} and not in_quote:
            in_quote = True
            quote_char = char
            current.append(char)
            continue
        if in_quote:
            current.append(char)
            if char == quote_char:
                in_quote = False
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)

    if current:
        parts.append("".join(current).strip())
    return parts


def _coerce_scalar(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
