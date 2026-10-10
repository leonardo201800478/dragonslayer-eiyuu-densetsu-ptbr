"""Audita frequências e contextos de marcadores Atlas sem alterar arquivos.

O relatório é lexical: não interpreta diretivas, não executa ferramentas externas
e não modifica scripts nem ROMs.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from dragonslayer_ptbr.text.atlas_segmenter import SegmentKind, classify_line

MARKER_KINDS = set(SegmentKind) - {SegmentKind.TEXT}


def audit_directory(root: Path, examples_per_marker: int = 3) -> dict[str, object]:
    """Conta marcadores e guarda exemplos de contexto textual para revisão manual."""
    if examples_per_marker < 0:
        raise ValueError("examples_per_marker deve ser maior ou igual a zero")
    if not root.is_dir():
        raise FileNotFoundError(f"Diretório não encontrado: {root}")

    scripts = sorted(root.glob("script_*.txt"))
    if not scripts:
        raise FileNotFoundError(f"Nenhum script_*.txt encontrado em: {root}")

    counts: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    decoding_errors: list[dict[str, str]] = []
    lines_processed = 0

    for path in scripts:
        try:
            content = path.read_bytes().decode("cp932")
        except UnicodeDecodeError as exc:
            decoding_errors.append({"file": path.name, "error": str(exc)})
            continue

        for line_number, raw in enumerate(content.splitlines(), start=1):
            lines_processed += 1
            result = classify_line(raw)
            text_context = "".join(
                segment.value
                for segment in result.segments
                if segment.kind is SegmentKind.TEXT
            )
            for segment in result.segments:
                if segment.kind not in MARKER_KINDS:
                    continue
                key = (segment.kind.value, segment.value)
                counts[key] += 1
                if len(examples[key]) < examples_per_marker:
                    examples[key].append(
                        {
                            "file": path.name,
                            "line": line_number,
                            "line_kind": result.kind.value,
                            "raw": raw,
                            "text_context": text_context,
                        }
                    )

    inventory = [
        {
            "kind": kind,
            "marker": marker,
            "count": count,
            "examples": examples[(kind, marker)],
        }
        for (kind, marker), count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
        )
    ]
    return {
        "schema_version": 1,
        "root": str(root.resolve()),
        "encoding": "cp932",
        "read_only": True,
        "scripts_found": len(scripts),
        "scripts_decoded": len(scripts) - len(decoding_errors),
        "lines_processed": lines_processed,
        "marker_occurrences": sum(counts.values()),
        "marker_types": len(counts),
        "marker_inventory": inventory,
        "decoding_errors": decoding_errors,
        "warning": (
            "Inventário lexical para revisão manual. Contexto textual não comprova "
            "a semântica do marcador; nenhuma ferramenta Atlas ou ROM é executada."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera inventário de marcadores Atlas e seus contextos."
    )
    parser.add_argument("directory", type=Path, help="diretório com script_*.txt")
    parser.add_argument("--examples", type=int, default=3, help="exemplos por marcador")
    args = parser.parse_args()
    if args.examples < 0:
        parser.error("--examples deve ser maior ou igual a zero")
    try:
        report = audit_directory(args.directory, args.examples)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["decoding_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
