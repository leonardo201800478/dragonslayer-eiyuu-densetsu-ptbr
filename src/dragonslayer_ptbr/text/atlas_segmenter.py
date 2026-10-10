"""Classificação conservadora de linhas e segmentos de scripts Atlas.

Este módulo é apenas um inspetor lexical: não interpreta nem executa diretivas
Atlas, não calcula ponteiros e não escreve em scripts ou ROMs. Marcadores não
reconhecidos permanecem preservados como segmentos UNKNOWN_MARKER.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class LineKind(str, Enum):
    DIRECTIVE = "DIRECTIVE"
    FILE_REFERENCE = "FILE_REFERENCE"
    COMMENT = "COMMENT"
    TEXT = "TEXT"
    MIXED = "MIXED"
    OTHER = "OTHER"


class SegmentKind(str, Enum):
    TEXT = "TEXT"
    DICTIONARY_MARKER = "DICTIONARY_MARKER"
    LINE_MARKER = "LINE_MARKER"
    CONTROL_FLOW_MARKER = "CONTROL_FLOW_MARKER"
    WAIT_MARKER = "WAIT_MARKER"
    COLOR_MARKER = "COLOR_MARKER"
    HERO_MARKER = "HERO_MARKER"
    FLAG_MARKER = "FLAG_MARKER"
    CODE_MARKER = "CODE_MARKER"
    NAME_MARKER = "NAME_MARKER"
    HEX_BYTE = "HEX_BYTE"
    UNKNOWN_MARKER = "UNKNOWN_MARKER"


INLINE_TOKEN = re.compile(r"<[^<>\r\n]+>")
JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
FILE_REFERENCE = re.compile(r"\[FILE\]", re.IGNORECASE)
DIRECTIVE = re.compile(r"^\s*#\w+")
COMMENT = re.compile(r"^\s*(?://|;)")
HEX_BYTE = re.compile(r"<\$[0-9A-Fa-f]{2}>")
DICTIONARY_MARKER = re.compile(r"<DICT\s+[0-9A-Fa-f]{2}>", re.IGNORECASE)

WAIT_MARKER = re.compile(r"<WAIT(?:\s+CLEAR)?>", re.IGNORECASE)
COLOR_MARKER = re.compile(r"<COLOR(?:\s+[0-9A-Fa-f]{2}|\s+OFF)>", re.IGNORECASE)
HERO_MARKER = re.compile(r"<HERO\s+[0-9]+>", re.IGNORECASE)
FLAG_MARKER = re.compile(r"<FLAG\s+[0-9A-Fa-f]{2}>", re.IGNORECASE)
CODE_MARKER = re.compile(r"<CODE\s+[0-9A-Fa-f]{2}>", re.IGNORECASE)
NAME_MARKER = re.compile(r"<NAME>", re.IGNORECASE)

CONTROL_FLOW_MARKERS = {
    "<JMP.L>",
    "<JMP>",
    "<RET>",
    "<END>",
    "<END 06>",
    "<RET *>",
}
CONTROL_FLOW_PARAMETERIZED = re.compile(r"<JMP\s+[0-9A-Fa-f]{2}>", re.IGNORECASE)
LINE_MARKERS = {"<LINE>"}


@dataclass(frozen=True, slots=True)
class Segment:
    kind: SegmentKind
    value: str


@dataclass(frozen=True, slots=True)
class ClassifiedLine:
    kind: LineKind
    raw: str
    segments: tuple[Segment, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "raw": self.raw,
            "segments": [
                {"kind": segment.kind.value, "value": segment.value}
                for segment in self.segments
            ],
        }


def classify_segment(value: str) -> SegmentKind:
    """Classifica sintaticamente um segmento sem alterar seu conteúdo."""
    if not INLINE_TOKEN.fullmatch(value):
        return SegmentKind.TEXT
    if DICTIONARY_MARKER.fullmatch(value):
        return SegmentKind.DICTIONARY_MARKER
    if value.upper() in LINE_MARKERS:
        return SegmentKind.LINE_MARKER
    if value.upper() in CONTROL_FLOW_MARKERS or CONTROL_FLOW_PARAMETERIZED.fullmatch(value):
        return SegmentKind.CONTROL_FLOW_MARKER
    if WAIT_MARKER.fullmatch(value):
        return SegmentKind.WAIT_MARKER
    if COLOR_MARKER.fullmatch(value):
        return SegmentKind.COLOR_MARKER
    if HERO_MARKER.fullmatch(value):
        return SegmentKind.HERO_MARKER
    if FLAG_MARKER.fullmatch(value):
        return SegmentKind.FLAG_MARKER
    if CODE_MARKER.fullmatch(value):
        return SegmentKind.CODE_MARKER
    if NAME_MARKER.fullmatch(value):
        return SegmentKind.NAME_MARKER
    if HEX_BYTE.fullmatch(value):
        return SegmentKind.HEX_BYTE
    return SegmentKind.UNKNOWN_MARKER


def classify_line(line: str) -> ClassifiedLine:
    """Classifica uma linha de script, preservando seu conteúdo textual."""
    if FILE_REFERENCE.search(line):
        return ClassifiedLine(LineKind.FILE_REFERENCE, line, ())
    if DIRECTIVE.match(line):
        return ClassifiedLine(LineKind.DIRECTIVE, line, ())
    if COMMENT.match(line) or line.lstrip().startswith("[TEXT]"):
        return ClassifiedLine(LineKind.COMMENT, line, ())

    segments: list[Segment] = []
    cursor = 0
    for match in INLINE_TOKEN.finditer(line):
        if match.start() > cursor:
            segments.append(Segment(SegmentKind.TEXT, line[cursor : match.start()]))
        token = match.group()
        segments.append(Segment(classify_segment(token), token))
        cursor = match.end()
    if cursor < len(line):
        segments.append(Segment(SegmentKind.TEXT, line[cursor:]))

    japanese_text = any(
        segment.kind == SegmentKind.TEXT and JAPANESE_TEXT.search(segment.value)
        for segment in segments
    )
    has_marker = any(segment.kind != SegmentKind.TEXT for segment in segments)

    if japanese_text and has_marker:
        kind = LineKind.MIXED
    elif japanese_text:
        kind = LineKind.TEXT
    else:
        kind = LineKind.OTHER

    return ClassifiedLine(kind, line, tuple(segments))


def classify_lines(lines: list[str]) -> list[ClassifiedLine]:
    """Classifica uma sequência de linhas sem modificar a entrada."""
    return [classify_line(line) for line in lines]


def result_to_dict(result: ClassifiedLine) -> dict[str, object]:
    """Retorna representação simples adequada para JSON."""
    return result.to_dict()


__all__ = [
    "ClassifiedLine",
    "LineKind",
    "Segment",
    "SegmentKind",
    "classify_line",
    "classify_lines",
    "classify_segment",
    "result_to_dict",
]
