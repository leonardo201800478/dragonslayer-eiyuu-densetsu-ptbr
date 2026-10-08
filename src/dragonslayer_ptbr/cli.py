from __future__ import annotations
import argparse
from pathlib import Path
from .analysis.rom import analyze_rom, write_report

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dslayer-ptbr", description="Ferramentas de análise e tradução.")
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("analyze", help="analisa uma ROM sem modificá-la")
    cmd.add_argument("--rom", required=True, type=Path)
    cmd.add_argument("--report", type=Path, default=Path("reports/rom-analysis.json"))
    return parser

def main() -> int:
    args = build_parser().parse_args()
    report = analyze_rom(args.rom)
    write_report(report, args.report)
    print(f"Análise concluída: {args.report}")
    print(f"Tamanho: {report['rom']['size']} bytes")
    print(f"CRC32: {report['rom']['crc32']}")
    print(f"SHA1: {report['rom']['sha1']}")
    print(f"Header Genesis: {'OK' if report['genesis_header']['valid'] else 'não confirmado'}")
    print(f"Regiões candidatas: {len(report['candidate_regions'])}")
    return 0
