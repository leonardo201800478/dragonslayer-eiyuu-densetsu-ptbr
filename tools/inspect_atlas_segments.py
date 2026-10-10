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
from collections import Counter
from pathlib import Path

from dragonslayer_ptbr.text.atlas_segmenter import (
    LineKind,
    SegmentKind,
    classify_line,
)


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

    report = {
        "root": str(root.resolve()),
        "encoding": "cp932",
        "read_only": True,
        "scripts_found": len(scripts),
        "scripts_decoded": len(scripts) - len(decoding_errors),
        "lines_processed": processed_lines,
        "line_counts": dict(line_counts),
        "segment_counts": dict(segment_counts),
        "examples_limit": limit,
        "examples": examples,
        "decoding_errors": decoding_errors,
        "warning": (
            "Classificação lexical experimental; UNKNOWN_MARKER e controles "
            "exigem validação contra os scripts e a documentação Atlas."
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
