from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dragonslayer_ptbr.text.script_codec import (
    EXTENDED_CONTROL,
    TERMINATOR,
    _decode_text_byte,
)


@dataclass(frozen=True)
class ControlOccurrence:
    """Ocorrência de um comando de script com offset absoluto na ROM."""

    offset: int
    raw: bytes

    @property
    def hex_bytes(self) -> str:
        """Retorna os bytes em hexadecimal legível."""
        return self.raw.hex(" ").upper()


def scan_script_controls(
    data: bytes,
    *,
    base_offset: int = 0,
    extended_control: int = EXTENDED_CONTROL,
    terminator: int = TERMINATOR,
) -> list[ControlOccurrence]:
    """Localiza controles preservando seus offsets e bytes originais.

    A rotina não atribui semântica aos comandos. O objetivo é produzir
    evidência auditável para a engenharia reversa do protocolo de script.
    """
    if base_offset < 0:
        raise ValueError("base_offset deve ser maior ou igual a zero")
    if not 0 <= extended_control <= 0xFF:
        raise ValueError("extended_control deve estar entre 0 e 255")
    if not 0 <= terminator <= 0xFF:
        raise ValueError("terminator deve estar entre 0 e 255")

    occurrences: list[ControlOccurrence] = []
    offset = 0

    while offset < len(data):
        value = data[offset]

        if value == terminator:
            occurrences.append(
                ControlOccurrence(base_offset + offset, data[offset : offset + 1])
            )
            offset += 1
            continue

        if value == extended_control:
            end = min(offset + 3, len(data))
            occurrences.append(ControlOccurrence(base_offset + offset, data[offset:end]))
            offset = end
            continue

        if value < 0x20:
            occurrences.append(
                ControlOccurrence(base_offset + offset, data[offset : offset + 1])
            )
            offset += 1
            continue

        decoded = _decode_text_byte(data, offset, "shift_jis")
        if decoded is None:
            offset += 1
            continue

        _, consumed = decoded
        offset += consumed

    return occurrences


def write_control_report(
    occurrences: list[ControlOccurrence],
    output: Path,
) -> None:
    """Escreve relatório textual determinístico das ocorrências."""
    output.parent.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for occurrence in occurrences:
        key = occurrence.hex_bytes
        counts[key] = counts.get(key, 0) + 1

    lines = [
        "# Script control report",
        "",
        f"Total de ocorrências: {len(occurrences)}",
        "",
        "## Frequência",
        "",
        "| Bytes | Ocorrências |",
        "|---|---:|",
    ]

    for raw, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{raw}` | {count} |")

    lines.extend(["", "## Ocorrências", "", "| Offset | Bytes |", "|---:|---|"])

    for occurrence in occurrences:
        lines.append(f"| `0x{occurrence.offset:06X}` | `{occurrence.hex_bytes}` |")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
