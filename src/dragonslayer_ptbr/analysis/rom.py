from __future__ import annotations

import hashlib
import json
import math
import zlib
from pathlib import Path
from typing import Any

from .pointers import scan_pointer_candidates
from .text_regions import scan_text_regions

DEFAULT_BLOCK_SIZE = 0x100


def _entropy(data: bytes) -> float:
    """Calcula a entropia de Shannon dos bytes fornecidos."""
    if not data:
        return 0.0

    counts = [0] * 256
    for value in data:
        counts[value] += 1

    size = len(data)
    return -sum(
        (count / size) * math.log2(count / size)
        for count in counts
        if count
    )


def _text_like_score(data: bytes) -> float:
    """Calcula uma pontuação simples para dados semelhantes a texto ASCII."""
    if not data:
        return 0.0

    printable = sum(
        1
        for value in data
        if value in (0, 10, 13) or 32 <= value <= 126
    )
    return printable / len(data)


def _runs(data: bytes, minimum: int = 8) -> list[dict[str, Any]]:
    """Localiza sequências contínuas com bytes compatíveis com ASCII."""
    regions: list[dict[str, Any]] = []
    start: int | None = None

    for index, value in enumerate(data):
        text_like = value in (0, 10, 13) or 32 <= value <= 126

        if text_like and start is None:
            start = index
        elif not text_like and start is not None:
            if index - start >= minimum:
                sample = data[start:index]
                regions.append(
                    {
                        "offset": start,
                        "end": index,
                        "size": index - start,
                        "score": round(_text_like_score(sample), 4),
                        "sample": sample[:80].decode("ascii", errors="replace"),
                    }
                )
            start = None

    if start is not None and len(data) - start >= minimum:
        sample = data[start:]
        regions.append(
            {
                "offset": start,
                "end": len(data),
                "size": len(data) - start,
                "score": round(_text_like_score(sample), 4),
                "sample": sample[:80].decode("ascii", errors="replace"),
            }
        )

    return regions


def _classify_block(data: bytes) -> str:
    """Classifica um bloco por características estatísticas, sem afirmar seu conteúdo."""
    if not data:
        return "empty"

    unique = len(set(data))
    zero_ratio = data.count(0) / len(data)
    ff_ratio = data.count(0xFF) / len(data)
    text_score = _text_like_score(data)
    entropy = _entropy(data)

    if zero_ratio >= 0.90:
        return "zero_fill"
    if ff_ratio >= 0.90:
        return "ff_fill"
    if text_score >= 0.85:
        return "ascii_like"
    if unique <= 4 and entropy <= 1.5:
        return "low_variation"
    if entropy >= 7.5:
        return "high_entropy"
    return "mixed"


def _scan_blocks(data: bytes, block_size: int = DEFAULT_BLOCK_SIZE) -> list[dict[str, Any]]:
    """Analisa a ROM em blocos fixos para revelar sua distribuição estrutural."""
    if block_size <= 0:
        raise ValueError("block_size deve ser maior que zero")

    blocks: list[dict[str, Any]] = []

    for offset in range(0, len(data), block_size):
        block = data[offset : offset + block_size]
        blocks.append(
            {
                "offset": offset,
                "end": offset + len(block),
                "size": len(block),
                "entropy": round(_entropy(block), 6),
                "zero_ratio": round(block.count(0) / len(block), 6),
                "ff_ratio": round(block.count(0xFF) / len(block), 6),
                "text_score": round(_text_like_score(block), 6),
                "unique_bytes": len(set(block)),
                "classification": _classify_block(block),
            }
        )

    return blocks


def _summarize_blocks(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """Resume a quantidade de blocos encontrada por classificação."""
    counts: dict[str, int] = {}

    for block in blocks:
        classification = block["classification"]
        counts[classification] = counts.get(classification, 0) + 1

    return {
        "block_count": len(blocks),
        "classifications": counts,
    }


def analyze_rom(
    path: Path,
    *,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> dict[str, Any]:
    """Analisa uma ROM sem modificá-la e produz metadados estruturais."""
    data = path.read_bytes()

    header = data[0x100:0x200] if len(data) >= 0x200 else b""
    console = header[0:16].rstrip(b" ") if header else b""
    name = header[0x10:0x40].rstrip(b" ") if len(header) >= 0x40 else b""
    serial = (
        header[0x80:0x8E].rstrip(b" \x00")
        if len(header) >= 0x8E
        else b""
    )

    blocks = _scan_blocks(data, block_size)

    return {
        "rom": {
            "path": str(path),
            "size": len(data),
            "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08X}",
            "sha1": hashlib.sha1(data).hexdigest().upper(),
        },
        "genesis_header": {
            "valid": console.startswith(b"SEGA"),
            "console": console.decode("ascii", "replace"),
            "domestic_name": name.decode("ascii", "replace"),
            "serial": serial.decode("ascii", "replace"),
        },
        "global": {
            "entropy": round(_entropy(data), 6),
            "zero_ratio": round(data.count(0) / len(data), 6) if data else 0.0,
            "ff_ratio": round(data.count(255) / len(data), 6) if data else 0.0,
            "unique_bytes": len(set(data)),
        },
        "structure": {
            "block_size": block_size,
            "summary": _summarize_blocks(blocks),
            "blocks": blocks,
        },
        "pointer_candidates": scan_pointer_candidates(data),
        "candidate_regions": _runs(data),
        "text_regions": scan_text_regions(data),
        "notes": [
            "Candidatos são heurísticos; não representam texto confirmado.",
            "Classificações estatísticas não determinam se um bloco é código, gráfico, texto ou dados comprimidos.",
            "Charset, compressão, ponteiros e códigos de controle serão determinados em etapas posteriores.",
            "Regiões text_regions são candidatos estruturais e não confirmam texto ou charset.",
        ],
    }


def write_report(report: dict[str, Any], path: Path) -> None:
    """Grava o relatório de análise em JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
