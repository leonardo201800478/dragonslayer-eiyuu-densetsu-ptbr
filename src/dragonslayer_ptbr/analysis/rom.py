from __future__ import annotations
import hashlib, json, math, zlib
from pathlib import Path
from typing import Any

def _entropy(data: bytes) -> float:
    if not data: return 0.0
    counts = [0] * 256
    for b in data: counts[b] += 1
    n = len(data)
    return -sum((c/n) * math.log2(c/n) for c in counts if c)

def _text_like_score(data: bytes) -> float:
    if not data: return 0.0
    good = sum(1 for b in data if b in (0, 10, 13) or 32 <= b <= 126)
    return good / len(data)

def _runs(data: bytes, minimum: int = 8) -> list[dict[str, Any]]:
    regions = []; start = None
    for i, b in enumerate(data):
        good = b in (0, 10, 13) or 32 <= b <= 126
        if good and start is None: start = i
        elif not good and start is not None:
            if i - start >= minimum:
                sample = data[start:i]
                regions.append({"offset": start, "end": i, "size": i-start, "score": round(_text_like_score(sample), 4), "sample": sample[:80].decode("ascii", errors="replace")})
            start = None
    return regions

def analyze_rom(path: Path) -> dict[str, Any]:
    """Analisa a imagem binária e retorna metadados sem alterá-la."""
    data = path.read_bytes()
    h = data[0x100:0x200] if len(data) >= 0x200 else b""
    console = h[0:16].rstrip(b" ") if h else b""
    name = h[0x10:0x40].rstrip(b" ") if len(h) >= 0x40 else b""
    serial = h[0x80:0x8E].rstrip(b" \x00") if len(h) >= 0x8E else b""
    return {"rom": {"path": str(path), "size": len(data), "crc32": f"{zlib.crc32(data)&0xffffffff:08X}", "sha1": hashlib.sha1(data).hexdigest().upper()},
            "genesis_header": {"valid": console.startswith(b"SEGA"), "console": console.decode("ascii", "replace"), "domestic_name": name.decode("ascii", "replace"), "serial": serial.decode("ascii", "replace")},
            "global": {"entropy": round(_entropy(data), 6), "zero_ratio": round(data.count(0)/len(data), 6), "ff_ratio": round(data.count(255)/len(data), 6)},
            "candidate_regions": _runs(data),
            "notes": ["Candidatos são heurísticos; não representam texto confirmado.", "Charset, compressão, ponteiros e códigos de controle serão determinados em etapas posteriores."]}

def write_report(report: dict[str, Any], path: Path) -> None:
    """Grava o relatório de análise em JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
