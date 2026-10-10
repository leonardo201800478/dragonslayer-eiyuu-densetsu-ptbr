"""Auditoria somente de leitura dos scripts de texto do Atlas.

Exemplo:
    python tools/audit_atlas_scripts.py reports/legacy-tooling-test/tools/text

O programa apenas lê arquivos TXT; não executa Atlas e não modifica ROMs
nem scripts de entrada.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PATTERNS: dict[str, re.Pattern[str]] = {
    "FILE": re.compile(r"\[FILE\]", re.IGNORECASE),
    "DIRETIVA_ATLAS": re.compile(r"^\s*#\w+"),
    "COMENTARIO": re.compile(r"^\s*(?://|;|\[TEXT\])"),
    "MARCADOR_INLINE": re.compile(r"<[^<>\r\n]+>"),
    "JAPONES": re.compile(r"[\u3040-\u30ff\u3400-\u9fff]"),
    "HEX_CONTROLE": re.compile(r"<\$[0-9A-Fa-f]{2}>"),
}
EXAMPLE_LIMIT = 4
DETAIL_FILES = {"script_00.txt", "script_01.txt"}


def audit(root: Path) -> int:
    """Classifica linhas dos scripts e imprime contagens e exemplos."""
    if not root.is_dir():
        print(f"Diretório não encontrado: {root.resolve()}", file=sys.stderr)
        return 2

    scripts = sorted(root.glob("script_*.txt"))
    if not scripts:
        print(f"Nenhum script_*.txt encontrado em: {root.resolve()}", file=sys.stderr)
        return 2

    totals: Counter[str] = Counter()
    examples: defaultdict[str, list[str]] = defaultdict(list)
    errors: list[tuple[str, str]] = []

    print(f"Diretório: {root.resolve()}")
    print(f"Scripts encontrados: {len(scripts)}")

    for path in scripts:
        try:
            content = path.read_bytes().decode("cp932")
        except UnicodeDecodeError as exc:
            errors.append((path.name, str(exc)))
            print(f"ERRO DE CODIFICAÇÃO: {path.name}: {exc}")
            continue

        counts: Counter[str] = Counter()
        for line_number, line in enumerate(content.splitlines(), start=1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    counts[label] += 1
                    totals[label] += 1
                    if len(examples[label]) < EXAMPLE_LIMIT:
                        examples[label].append(
                            f"{path.name}:{line_number}: {line[:180]}"
                        )

        if path.name in DETAIL_FILES:
            print(f"\n[{path.name}]")
            for label, count in counts.most_common():
                print(f"  {label}: {count}")

    print("\n=== EXEMPLOS POR CATEGORIA ===")
    for label in PATTERNS:
        if not examples[label]:
            continue
        print(f"\n{label}:")
        for example in examples[label]:
            print(f"  {example}")

    print("\n=== TOTAIS DO LOTE ===")
    for label, count in totals.most_common():
        print(f"{label}: {count}")

    print(f"\nArquivos com erro de decodificação: {len(errors)}")
    for filename, error in errors:
        print(f"  {filename}: {error}")

    print("Auditoria concluída; nenhum arquivo foi alterado.")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita scripts Atlas em CP932 sem modificar os arquivos."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path("reports/legacy-tooling-test/tools/text"),
        help="diretório com os arquivos script_*.txt",
    )
    args = parser.parse_args()
    return audit(args.directory)


if __name__ == "__main__":
    raise SystemExit(main())
