"""Classificação conservadora de linhas e segmentos de scripts Atlas.

Este módulo é apenas um inspetor lexical: não interpreta nem executa diretivas
Atlas, não calcula ponteiros e não escreve em scripts ou ROMs. Marcadores não
reconhecidos permanecem preservados como segmentos UNKNOWN_MARKER.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import StrEnum


class LineKind(StrEnum):
    DIRECTIVE = "DIRECTIVE"
    FILE_REFERENCE = "FILE_REFERENCE"
    COMMENT = "COMMENT"
    TEXT = "TEXT"
    MIXED = "MIXED"
    OTHER = "OTHER"


class SegmentKind(StrEnum):
    TEXT = "TEXT"
    DICTIONARY_MARKER = "DICTIONARY_MARKER"
    LINE_MARKER = "LINE_MARKER"
    CONTROL_FLOW_MARKER = "CONTROL_FLOW_MARKER"
    HEX_BYTE = "HEX_BYTE"
    KNOWN_MARKER = "KNOWN_MARKER"
    UNKNOWN_MARKER = "UNKNOWN_MARKER"


INLINE_TOKEN = re.compile(r"<[^<>\r\n]+>")
JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
FILE_REFERENCE = re.compile(r"\[FILE\]", re.IGNORECASE)
DIRECTIVE = re.compile(r"^\s*#\w+")
COMMENT = re.compile(r"^\s*(?://|;)")
HEX_BYTE = re.compile(r"<\$[0-9A-Fa-f]{2}>")
DICTIONARY_MARKER = re.compile(r"<DICT\s+[0-9A-Fa-f]{2}>", re.IGNORECASE)

CONTROL_FLOW_MARKERS = {
    "<JMP.L>",
    "<JMP>",
    "<RET>",
    "<END>",
}
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
    """Classifica um segmento sem remover nem normalizar seu conteúdo."""
    if not INLINE_TOKEN.fullmatch(value):
        return SegmentKind.TEXT
    if DICTIONARY_MARKER.fullmatch(value):
        return SegmentKind.DICTIONARY_MARKER
    if value.upper() in LINE_MARKERS:
        return SegmentKind.LINE_MARKER
    if value.upper() in CONTROL_FLOW_MARKERS:
        return SegmentKind.CONTROL_FLOW_MARKER
    if HEX_BYTE.fullmatch(value):
        return SegmentKind.HEX_BYTE
    if value.upper() in {"<END 06>", "<RET *>"}:
        return SegmentKind.CONTROL_FLOW_MARKER
    return SegmentKind.UNKNOWN_MARKER


def classify_line(line: str) -> ClassifiedLine:
    """Classifica uma linha de script, preservando seu conteúdo byte-textual."""
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

    if not segments:
        kind = LineKind.OTHER
    elif any(segment.kind == SegmentKind.TEXT and JAPANESE_TEXT.search(segment.value) for segment in segments):
        has_marker = any(segment.kind != SegmentKind.TEXT for segment in segments)
        kind = LineKind.MIXED if has_marker else LineKind.TEXT
    elif any(segment.kind != SegmentKind.TEXT for segment in segments):
        kind = LineKind.OTHER
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
