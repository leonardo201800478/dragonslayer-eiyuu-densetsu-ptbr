from __future__ import annotations

import argparse
from pathlib import Path

from .analysis.rom import DEFAULT_BLOCK_SIZE, analyze_rom, write_report
from .analysis.script_controls import scan_script_controls, write_control_report
from .analysis.m68k_references import scan_known_targets, write_reference_report
from .text.script_codec import render_script, tokenize_script


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

    controls = sub.add_parser(
        "scan-controls",
        help="mapeia controles de uma região de script sem atribuir semântica",
    )
    controls.add_argument("--rom", required=True, type=Path)
    controls.add_argument(
        "--offset",
        required=True,
        type=lambda value: int(value, 0),
        help="offset inicial em bytes; aceita decimal ou hexadecimal",
    )
    controls.add_argument(
        "--size",
        required=True,
        type=lambda value: int(value, 0),
        help="quantidade de bytes; aceita decimal ou hexadecimal",
    )
    controls.add_argument(
        "--output",
        type=Path,
        default=Path("reports/script-controls.md"),
        help="relatório Markdown de saída",
    )

    decode = sub.add_parser(
        "decode-text",
        help="decodifica uma região confirmada do script sem modificar a ROM",
    )
    decode.add_argument("--rom", required=True, type=Path)
    decode.add_argument(
        "--offset",
        required=True,
        type=lambda value: int(value, 0),
        help="offset inicial em bytes; aceita decimal ou hexadecimal",
    )
    decode.add_argument(
        "--size",
        required=True,
        type=lambda value: int(value, 0),
        help="quantidade de bytes; aceita decimal ou hexadecimal",
    )
    decode.add_argument(
        "--output",
        type=Path,
        help="arquivo de saída UTF-8; se omitido, escreve no console",
    )
    decode.add_argument(
        "--stop-at-terminator",
        action="store_true",
        help="para no primeiro terminador 0x00",
    )


    refs = sub.add_parser(
        "scan-refs",
        help="procura referências 68000 a offsets confirmados da ROM",
    )
    refs.add_argument("--rom", required=True, type=Path)
    refs.add_argument(
        "--output",
        type=Path,
        default=Path("reports/m68k-references.md"),
    )
    refs.add_argument(
        "--context",
        type=lambda value: int(value, 0),
        default=8,
        help="bytes de contexto em cada lado (padrão: 8)",
    )

    return parser


def main() -> int:
    """Executa o comando solicitado e retorna seu código de saída."""
    args = build_parser().parse_args()

    if not args.rom.is_file():
        raise SystemExit(f"ROM não encontrada: {args.rom}")

    if args.command == "scan-refs":
        if args.context < 0:
            raise SystemExit("context deve ser maior ou igual a zero")

        data = args.rom.read_bytes()
        references = scan_known_targets(
            data,
            {
                "opening_script": 0x01626B,
                "character_table": 0x1A551A,
            },
            context_size=args.context,
        )
        write_reference_report(references, args.output)
        for name, items in references.items():
            print(f"{name}: {len(items)} referências")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-controls":
        if args.offset < 0:
            raise SystemExit("offset deve ser maior ou igual a zero")
        if args.size <= 0:
            raise SystemExit("size deve ser maior que zero")

        data = args.rom.read_bytes()
        end = args.offset + args.size
        if end > len(data):
            raise SystemExit("a região solicitada ultrapassa o tamanho da ROM")

        occurrences = scan_script_controls(
            data[args.offset:end],
            base_offset=args.offset,
        )
        write_control_report(occurrences, args.output)
        print(f"Controles encontrados: {len(occurrences)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "decode-text":
        if args.offset < 0:
            raise SystemExit("offset deve ser maior ou igual a zero")
        if args.size <= 0:
            raise SystemExit("size deve ser maior que zero")

        data = args.rom.read_bytes()
        end = args.offset + args.size
        if end > len(data):
            raise SystemExit("a região solicitada ultrapassa o tamanho da ROM")

        tokens = tokenize_script(
            data[args.offset:end],
            stop_at_terminator=args.stop_at_terminator,
        )
        rendered = render_script(tokens)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Texto decodificado: {args.output}")
        else:
            print(rendered)
        return 0

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

    pointer_candidates = report["pointer_candidates"]
    print("Candidatos a ponteiros:")
    for width in ("16_bit", "24_bit", "32_bit"):
        info = pointer_candidates[width]
        print(
            f"  - {width}: {info['candidate_count']} destinos repetidos; "
            f"{len(info['tables'])} tabelas candidatas"
        )

    print(f"Regiões textuais candidatas: {len(report['text_regions'])}")

    classifications = report["structure"]["summary"]["classifications"]
    if classifications:
        print("Classificações:")
        for name, count in sorted(classifications.items()):
            print(f"  - {name}: {count}")

    return 0
