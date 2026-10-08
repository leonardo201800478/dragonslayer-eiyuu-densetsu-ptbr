from __future__ import annotations

from collections import Counter
from typing import Any


def _read_uint(data: bytes, offset: int, width: int) -> int:
    """Lê um inteiro big-endian no formato natural do 68000."""
    return int.from_bytes(data[offset : offset + width], byteorder="big", signed=False)


def _pointer_target(value: int, rom_size: int, width: int) -> int | None:
    """Converte um valor candidato em offset de ROM quando ele for válido."""
    # Zero e valores de preenchimento não são úteis como candidatos: em regiões
    # vazias eles dominariam a contagem sem representar referências reais.
    if 0 < value < rom_size:
        return value

    # Alguns formatos podem armazenar o endereço lógico com bit de mapeamento.
    # Esta conversão é deliberadamente limitada: só remove o bit 24 de um
    # endereço de 68000 quando o restante aponta para dentro da imagem.
    if width == 4 and 0xFF000000 <= value <= 0xFFFFFFFF:
        target = value & 0x00FFFFFF
        if target < rom_size:
            return target

    return None


def _scan_pointer_width(
    data: bytes,
    width: int,
    *,
    alignment: int = 2,
    minimum_references: int = 2,
) -> dict[str, Any]:
    """Procura valores big-endian que apontem para offsets válidos da ROM."""
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


def scan_pointer_candidates(
    data: bytes,
    *,
    minimum_references: int = 2,
) -> dict[str, Any]:
    """Analisa candidatos a ponteiros 16, 24 e 32-bit sem alterar a ROM."""
    if minimum_references < 1:
        raise ValueError("minimum_references deve ser maior que zero")

    return {
        "notes": [
            "Candidatos são heurísticos e não representam ponteiros confirmados.",
            "O alvo zero é excluído para evitar falsos positivos causados por regiões preenchidas com 00.",
            "A análise usa big-endian, coerente com a representação binária usual do 68000.",
            "Valores coincidentes com offsets válidos podem ser dados comuns, não ponteiros.",
        ],
        "16_bit": _scan_pointer_width(
            data,
            2,
            alignment=2,
            minimum_references=minimum_references,
        ),
        "24_bit": _scan_pointer_width(
            data,
            3,
            alignment=1,
            minimum_references=minimum_references,
        ),
        "32_bit": _scan_pointer_width(
            data,
            4,
            alignment=2,
            minimum_references=minimum_references,
        ),
    }
