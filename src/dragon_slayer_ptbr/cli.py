"""Interface de linha de comando."""

from __future__ import annotations

import argparse
from pathlib import Path

from .patch import PatchError, apply_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dslayer-ptbr",
        description="Aplica um manifesto de patch validado a uma cópia de ROM.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply_parser = subparsers.add_parser("apply", help="aplica um manifesto JSON")
    apply_parser.add_argument("--rom", required=True, type=Path, help="caminho da ROM de entrada")
    apply_parser.add_argument("--manifest", required=True, type=Path, help="manifesto JSON")
    apply_parser.add_argument("--output", required=True, type=Path, help="arquivo de saída")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        count = apply_manifest(args.rom, args.manifest, args.output)
    except PatchError as exc:
        print(f"Erro: {exc}", file=__import__("sys").stderr)
        return 1
    print(f"Patch aplicado: {count} alteração(ões) gravada(s) em {args.output}.")
    return 0
