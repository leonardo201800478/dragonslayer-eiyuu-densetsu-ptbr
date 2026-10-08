from __future__ import annotations

import math
from collections import Counter
from typing import Any

DEFAULT_MIN_REGION_SIZE = 4
DEFAULT_MAX_REGION_SIZE = 512
DEFAULT_MIN_CANDIDATE_SCORE = 0.55


def _byte_entropy(data: bytes) -> float:
    """Calcula a entropia de Shannon de uma região."""
    if not data:
        return 0.0

    counts = Counter(data)
    size = len(data)
    return -sum(
        (count / size) * math.log2(count / size)
        for count in counts.values()
    )


def _delimiter_runs(
    data: bytes,
    *,
    delimiter: int,
    minimum_size: int,
    maximum_size: int,
) -> list[dict[str, Any]]:
    """Extrai regiões separadas por um byte delimitador."""
    runs: list[dict[str, Any]] = []
    start = 0

    for offset, value in enumerate(data):
        if value != delimiter:
            continue

        size = offset - start
        if minimum_size <= size <= maximum_size:
            runs.append(
                {
                    "offset": start,
                    "end": offset,
                    "size": size,
                    "delimiter": delimiter,
                    "data": data[start:offset],
                }
            )
        start = offset + 1

    if start < len(data):
        size = len(data) - start
        if minimum_size <= size <= maximum_size:
            runs.append(
                {
                    "offset": start,
                    "end": len(data),
                    "size": size,
                    "delimiter": None,
                    "data": data[start:],
                }
            )

    return runs


def _candidate_score(data: bytes, delimiter: int | None) -> tuple[float, list[str]]:
    """Calcula evidências heurísticas sem assumir um charset."""
    if not data:
        return 0.0, []

    size = len(data)
    unique = len(set(data))
    entropy = _byte_entropy(data)
    zero_ratio = data.count(0) / size
    ff_ratio = data.count(0xFF) / size
    control_ratio = sum(value < 0x20 for value in data) / size
    ascii_ratio = sum(32 <= value <= 126 for value in data) / size

    score = 0.0
    evidence: list[str] = []

    if delimiter is not None:
        score += 0.25
        evidence.append(f"terminador 0x{delimiter:02X}")

    if 0.15 <= unique / size <= 0.85:
        score += 0.15
        evidence.append("diversidade de bytes compatível com dados simbólicos")

    if 1.5 <= entropy <= 6.5:
        score += 0.15
        evidence.append("entropia intermediária")
    if ff_ratio > 0.20:
        score -= 0.40
        evidence.append("alto preenchimento FF")

    if zero_ratio <= 0.20 and ff_ratio <= 0.20:
        score += 0.10
        evidence.append("baixo preenchimento 00/FF")

    if ascii_ratio >= 0.35:
        score += 0.25
        evidence.append("presença significativa de ASCII")
    elif control_ratio <= 0.25:
        score += 0.15
        evidence.append("baixa concentração de bytes de controle")

    if 8 <= size <= 256:
        score += 0.10
        evidence.append("tamanho compatível com uma unidade textual")

    return min(score, 1.0), evidence


def scan_text_regions(
    data: bytes,
    *,
    minimum_size: int = DEFAULT_MIN_REGION_SIZE,
    maximum_size: int = DEFAULT_MAX_REGION_SIZE,
    minimum_score: float = DEFAULT_MIN_CANDIDATE_SCORE,
    delimiters: tuple[int, ...] = (0x00,),
) -> list[dict[str, Any]]:
    """Localiza regiões estruturalmente compatíveis com dados textuais.

    A função não assume ASCII, Shift-JIS ou um charset específico. Os
    resultados são candidatos heurísticos e precisam ser validados contra
    o conteúdo real da ROM.
    """
    if minimum_size < 1:
        raise ValueError("minimum_size deve ser maior que zero")
    if maximum_size < minimum_size:
        raise ValueError("maximum_size deve ser maior ou igual a minimum_size")
    if not 0.0 <= minimum_score <= 1.0:
        raise ValueError("minimum_score deve estar entre 0 e 1")
    if not delimiters:
        raise ValueError("delimiters não pode ser vazio")

    candidates: list[dict[str, Any]] = []

    for delimiter in delimiters:
        for region in _delimiter_runs(
            data,
            delimiter=delimiter,
            minimum_size=minimum_size,
            maximum_size=maximum_size,
        ):
            score, evidence = _candidate_score(region["data"], delimiter)
            if score < minimum_score:
                continue

            sample = region["data"][:64]
            candidates.append(
                {
                    "offset": region["offset"],
                    "end": region["end"],
                    "size": region["size"],
                    "delimiter": delimiter,
                    "score": round(score, 4),
                    "entropy": round(_byte_entropy(region["data"]), 6),
                    "unique_bytes": len(set(region["data"])),
                    "ascii_ratio": round(
                        sum(32 <= value <= 126 for value in region["data"])
                        / region["size"],
                        6,
                    ),
                    "sample_hex": sample.hex(" ").upper(),
                    "evidence": evidence,
                }
            )

    candidates.sort(key=lambda item: (-item["score"], item["offset"]))

    unique: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for candidate in candidates:
        key = (candidate["offset"], candidate["end"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)

    return unique
