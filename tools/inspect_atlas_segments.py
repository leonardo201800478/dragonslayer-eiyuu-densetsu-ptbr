"""Gera relatório JSON de classificação lexical dos scripts Atlas.

Exemplo:
    python tools/inspect_atlas_segments.py reports/legacy-tooling-test/tools/text
    python tools/inspect_atlas_segments.py reports/legacy-tooling-test/tools/text --limit 20

Somente leitura: não executa Atlas, não modifica scripts e não acessa ROMs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from dragonslayer_ptbr.text.atlas_segmenter import (
    LineKind,
    SegmentKind,
    classify_line,
)

UNKNOWN_EXAMPLES_PER_MARKER = 3


def inspect_directory(root: Path, limit: int) -> int:
    if not root.is_dir():
        print(f"Diretório não encontrado: {root.resolve()}", file=sys.stderr)
        return 2

    scripts = sorted(root.glob("script_*.txt"))
    if not scripts:
        print(f"Nenhum script_*.txt encontrado em: {root.resolve()}", file=sys.stderr)
        return 2

    line_counts: Counter[str] = Counter()
    segment_counts: Counter[str] = Counter()
    unknown_counts: Counter[str] = Counter()
    unknown_examples: dict[str, list[dict[str, object]]] = defaultdict(list)
    examples: list[dict[str, object]] = []
    decoding_errors: list[dict[str, str]] = []
    processed_lines = 0

    for path in scripts:
        try:
            text = path.read_bytes().decode("cp932")
        except UnicodeDecodeError as exc:
            decoding_errors.append({"file": path.name, "error": str(exc)})
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            result = classify_line(line)
            line_counts[result.kind.value] += 1
            processed_lines += 1
            for segment in result.segments:
                segment_counts[segment.kind.value] += 1
                if segment.kind is SegmentKind.UNKNOWN_MARKER:
                    unknown_counts[segment.value] += 1
                    marker_examples = unknown_examples[segment.value]
                    if len(marker_examples) < UNKNOWN_EXAMPLES_PER_MARKER:
                        marker_examples.append(
                            {
                                "file": path.name,
                                "line": line_number,
                                "line_kind": result.kind.value,
                                "raw": line,
                            }
                        )

            if (
                len(examples) < limit
                and result.kind in {LineKind.MIXED, LineKind.TEXT}
            ):
                examples.append(
                    {
                        "file": path.name,
                        "line": line_number,
                        "classification": result.to_dict(),
                    }
                )

    unknown_markers = [
        {
            "marker": marker,
            "count": count,
            "examples": unknown_examples[marker],
        }
        for marker, count in sorted(
            unknown_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    report = {
        "root": str(root.resolve()),
        "encoding": "cp932",
        "read_only": True,
        "scripts_found": len(scripts),
        "scripts_decoded": len(scripts) - len(decoding_errors),
        "lines_processed": processed_lines,
        "line_counts": dict(line_counts),
        "segment_counts": dict(segment_counts),
        "unknown_marker_occurrences": sum(unknown_counts.values()),
        "unknown_marker_types": len(unknown_counts),
        "unknown_marker_examples_per_type": UNKNOWN_EXAMPLES_PER_MARKER,
        "unknown_markers": unknown_markers,
        "examples_limit": limit,
        "examples": examples,
        "decoding_errors": decoding_errors,
        "warning": (
            "Classificação lexical experimental. UNKNOWN_MARKER é uma categoria "
            "sintática, não um erro confirmado; valide os exemplos contra os "
            "scripts e a documentação Atlas. Comentários não são segmentados."
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if decoding_errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspeciona segmentos Atlas em CP932 sem alterar arquivos."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="diretório que contém script_*.txt",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="quantidade máxima de exemplos de linhas textuais (padrão: 12)",
    )
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit deve ser maior ou igual a zero")
    return inspect_directory(args.directory, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
