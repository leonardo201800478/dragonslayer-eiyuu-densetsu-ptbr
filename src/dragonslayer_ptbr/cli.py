from __future__ import annotations

import argparse
from pathlib import Path

from .analysis.rom import DEFAULT_BLOCK_SIZE, analyze_rom, write_report


def build_parser() -> argparse.ArgumentParser:
    """Cria a interface de linha de comando do projeto."""
    parser = argparse.ArgumentParser(
        prog="dslayer-ptbr",
        description="Ferramentas de análise e tradução.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser(
        "analyze",
        help="analisa uma ROM sem modificá-la",
    )
    command.add_argument("--rom", required=True, type=Path)
    command.add_argument(
        "--report",
        type=Path,
        default=Path("reports/rom-analysis.json"),
    )
    command.add_argument(
        "--block-size",
        type=lambda value: int(value, 0),
        default=DEFAULT_BLOCK_SIZE,
        help="tamanho dos blocos em bytes; aceita decimal ou hexadecimal (padrão: 0x100)",
    )

    return parser


def main() -> int:
    """Executa o comando solicitado e retorna seu código de saída."""
    args = build_parser().parse_args()

    if not args.rom.is_file():
        raise SystemExit(f"ROM não encontrada: {args.rom}")

    report = analyze_rom(args.rom, block_size=args.block_size)
    write_report(report, args.report)

    print(f"Análise concluída: {args.report}")
    print(f"Tamanho: {report['rom']['size']} bytes")
    print(f"CRC32: {report['rom']['crc32']}")
    print(f"SHA1: {report['rom']['sha1']}")
    print(
        "Header Genesis: "
        f"{'OK' if report['genesis_header']['valid'] else 'não confirmado'}"
    )
    print(f"Blocos analisados: {report['structure']['summary']['block_count']}")
    print(f"Regiões candidatas: {len(report['candidate_regions'])}")

    classifications = report["structure"]["summary"]["classifications"]
    if classifications:
        print("Classificações:")
        for name, count in sorted(classifications.items()):
            print(f"  - {name}: {count}")

    return 0
