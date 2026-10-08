from __future__ import annotations

from collections import Counter
from typing import Any

MIN_ROM_TARGET = 0x200
MAX_TABLE_TARGET_DELTA = 0x4000


def _read_uint(data: bytes, offset: int, width: int) -> int:
    """Lê um inteiro big-endian no formato natural do Motorola 68000."""
    return int.from_bytes(data[offset : offset + width], byteorder="big", signed=False)


def _pointer_target(value: int, rom_size: int, width: int) -> int | None:
    """Converte um valor bruto em offset de ROM quando o formato permitir."""
    if MIN_ROM_TARGET <= value < rom_size:
        return value

    if width == 4 and 0xFF000000 <= value <= 0xFFFFFFFF:
        target = value & 0x00FFFFFF
        if MIN_ROM_TARGET <= target < rom_size:
            return target

    return None


def _scan_pointer_width(
    data: bytes,
    width: int,
    *,
    alignment: int = 2,
    minimum_references: int = 2,
) -> dict[str, Any]:
    """Mede referências brutas, mas só promove destinos repetidos a candidatos."""
    counts: Counter[int] = Counter()
    locations: dict[int, list[int]] = {}

    for offset in range(0, len(data) - width + 1, alignment):
        value = _read_uint(data, offset, width)
        target = _pointer_target(value, len(data), width)
        if target is None:
            continue
        counts[target] += 1
        locations.setdefault(target, []).append(offset)

    candidates = []
    for target, count in counts.most_common():
        if count < minimum_references:
            continue
        refs = locations[target]
        candidates.append(
            {
                "target": target,
                "target_hex": f"0x{target:06X}",
                "references": count,
                "reference_offsets": refs[:32],
                "reference_offsets_hex": [f"0x{x:06X}" for x in refs[:32]],
            }
        )

    return {
        "width": width,
        "byte_order": "big",
        "alignment": alignment,
        "minimum_references": minimum_references,
        "candidate_count": len(candidates),
        "candidates": candidates[:1000],
    }


def _scan_pointer_tables(
    data: bytes,
    width: int,
    *,
    alignment: int,
    minimum_entries: int = 4,
    max_target_delta: int = MAX_TABLE_TARGET_DELTA,
) -> list[dict[str, Any]]:
    """Procura tabelas de ponteiros com evidências estruturais conservadoras.

    Uma sequência apenas crescente não é suficiente: dados numéricos da ROM
    produzem esse padrão com frequência. As entradas precisam apontar para a
    área útil da ROM, crescer estritamente e não apresentar saltos excessivos
    entre destinos consecutivos.
    """
    entries: list[tuple[int, int]] = []
    for offset in range(0, len(data) - width + 1, alignment):
        value = _read_uint(data, offset, width)
        target = _pointer_target(value, len(data), width)
        entries.append((offset, target if target is not None else -1))

    tables: list[dict[str, Any]] = []
    start = 0
    while start < len(entries):
        if entries[start][1] < 0:
            start += 1
            continue

        end = start + 1
        while end < len(entries):
            previous_target = entries[end - 1][1]
            current_target = entries[end][1]
            if current_target < 0:
                break
            delta = current_target - previous_target
            if delta <= 0 or delta > max_target_delta:
                break
            end += 1

        length = end - start
        if length >= minimum_entries:
            offsets = [item[0] for item in entries[start:end]]
            targets = [item[1] for item in entries[start:end]]
            deltas = [targets[index] - targets[index - 1] for index in range(1, len(targets))]
            tables.append(
                {
                    "start": offsets[0],
                    "start_hex": f"0x{offsets[0]:06X}",
                    "end": offsets[-1] + width,
                    "end_hex": f"0x{offsets[-1] + width:06X}",
                    "entries": length,
                    "targets": targets[:64],
                    "targets_hex": [f"0x{x:06X}" for x in targets[:64]],
                    "target_span": targets[-1] - targets[0],
                    "min_delta": min(deltas),
                    "max_delta": max(deltas),
                }
            )
        start = end

    return tables[:1000]


def scan_pointer_candidates(
    data: bytes,
    *,
    minimum_references: int = 2,
    minimum_table_entries: int = 4,
    max_table_target_delta: int = MAX_TABLE_TARGET_DELTA,
) -> dict[str, Any]:
    """Analisa candidatos a ponteiros e tabelas sem alterar a ROM."""
    if minimum_references < 1:
        raise ValueError("minimum_references deve ser maior que zero")
    if minimum_table_entries < 2:
        raise ValueError("minimum_table_entries deve ser maior que um")
    if max_table_target_delta <= 0:
        raise ValueError("max_table_target_delta deve ser maior que zero")

    result: dict[str, Any] = {
        "notes": [
            "Candidatos são heurísticos e não representam ponteiros confirmados.",
            "A análise usa big-endian, coerente com a representação binária usual do 68000.",
            "O alvo zero e a região inicial da ROM são excluídos para reduzir ruído estrutural.",
            "Valores 16-bit são especialmente ambíguos em ROMs de 2 MiB; repetição isolada não confirma uma tabela.",
            "Tabelas exigem crescimento estrito e limite de distância entre destinos; sequências apenas monotônicas são rejeitadas.",
        ],
        "table_detection": {
            "minimum_target": MIN_ROM_TARGET,
            "minimum_entries": minimum_table_entries,
            "max_target_delta": max_table_target_delta,
        },
    }

    for name, width, alignment in (("16_bit", 2, 2), ("24_bit", 3, 1), ("32_bit", 4, 2)):
        result[name] = _scan_pointer_width(
            data, width, alignment=alignment, minimum_references=minimum_references
        )
        result[name]["tables"] = _scan_pointer_tables(
            data,
            width,
            alignment=alignment,
            minimum_entries=minimum_table_entries,
            max_target_delta=max_table_target_delta,
        )

    return result
