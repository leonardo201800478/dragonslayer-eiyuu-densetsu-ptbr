from __future__ import annotations

import argparse
from pathlib import Path

from .analysis.japanese_text import scan_japanese_text, write_japanese_text_report
from .analysis.m68k_a3_flow import (
    scan_a3_byte_reads,
    scan_a3_definitions,
    write_a3_report,
)
from .analysis.m68k_code import build_control_flow_graph, write_code_report
from .analysis.m68k_control_tests import scan_control_tests, write_control_test_report
from .analysis.m68k_entry_overlap import DEFAULT_ENTRIES, write_entry_overlap_report
from .analysis.m68k_indexed_reads import (
    scan_indexed_byte_reads,
    write_indexed_byte_report,
)
from .analysis.m68k_reachable_text import (
    scan_reachable_text_candidates,
    write_reachable_text_report,
)
from .analysis.m68k_references import scan_known_targets, write_reference_report
from .analysis.m68k_register_flow import trace_register_flow, write_register_flow_report
from .analysis.m68k_target_inspector import DEFAULT_TARGETS, write_target_inspection_report
from .analysis.m68k_text_parser_candidates import (
    scan_text_parser_candidates,
    write_text_parser_report,
)
from .analysis.rom import DEFAULT_BLOCK_SIZE, analyze_rom, write_report
from .analysis.script_controls import scan_script_controls, write_control_report
from .text.script_codec import render_script, tokenize_script


def build_parser() -> argparse.ArgumentParser:
    """Cria a interface de linha de comando do projeto."""
    parser = argparse.ArgumentParser(
        prog="dslayer-ptbr",
        description="Ferramentas de análise e tradução.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("analyze", help="analisa uma ROM sem modificá-la")
    command.add_argument("--rom", required=True, type=Path)
    command.add_argument("--report", type=Path, default=Path("reports/rom-analysis.json"))
    command.add_argument(
        "--block-size",
        type=lambda value: int(value, 0),
        default=DEFAULT_BLOCK_SIZE,
        help="tamanho dos blocos em bytes; aceita decimal ou hexadecimal",
    )

    controls = sub.add_parser(
        "scan-controls",
        help="mapeia controles de uma região de script sem atribuir semântica",
    )
    controls.add_argument("--rom", required=True, type=Path)
    controls.add_argument("--offset", required=True, type=lambda value: int(value, 0))
    controls.add_argument("--size", required=True, type=lambda value: int(value, 0))
    controls.add_argument(
        "--output", type=Path, default=Path("reports/script-controls.md")
    )

    decode = sub.add_parser(
        "decode-text",
        help="decodifica uma região confirmada do script sem modificar a ROM",
    )
    decode.add_argument("--rom", required=True, type=Path)
    decode.add_argument("--offset", required=True, type=lambda value: int(value, 0))
    decode.add_argument("--size", required=True, type=lambda value: int(value, 0))
    decode.add_argument("--output", type=Path)
    decode.add_argument("--stop-at-terminator", action="store_true")

    refs = sub.add_parser(
        "scan-refs",
        help="procura referências 68000 a offsets confirmados da ROM",
    )
    refs.add_argument("--rom", required=True, type=Path)
    refs.add_argument("--output", type=Path, default=Path("reports/m68k-references.md"))
    refs.add_argument("--context", type=lambda value: int(value, 0), default=8)

    control_tests = sub.add_parser(
        "scan-control-tests",
        help="localiza comparações 68000 explícitas com bytes de controle",
    )
    control_tests.add_argument("--rom", required=True, type=Path)
    control_tests.add_argument(
        "--output", type=Path, default=Path("reports/m68k-control-tests.md")
    )
    control_tests.add_argument("--context", type=lambda value: int(value, 0), default=12)

    parser_candidates = sub.add_parser(
        "scan-text-parser-candidates",
        help="localiza leitura de byte seguida de comparação de controle",
    )
    parser_candidates.add_argument("--rom", required=True, type=Path)
    parser_candidates.add_argument("--output", type=Path, default=Path(
        "reports/m68k-text-parser-candidates.md"
    ))
    parser_candidates.add_argument("--max-distance", type=lambda value: int(value, 0), default=16)
    parser_candidates.add_argument("--context", type=lambda value: int(value, 0), default=16)

    reachable_text = sub.add_parser(
        "scan-reachable-text",
        help="cruza leituras e controles apenas nos blocos do CFG alcançável",
    )
    reachable_text.add_argument("--rom", required=True, type=Path)
    reachable_text.add_argument(
        "--output", type=Path, default=Path("reports/m68k-reachable-text.md")
    )
    reachable_text.add_argument("--max-distance", type=lambda value: int(value, 0), default=16)

    a3_flow = sub.add_parser("scan-a3-flow", help="mapeia definições e leituras do registrador A3")
    a3_flow.add_argument("--rom", required=True, type=Path)
    a3_flow.add_argument("--output", type=Path, default=Path("reports/m68k-a3-flow.md"))
    a3_flow.add_argument("--context", type=lambda value: int(value, 0), default=12)

    code_flow = sub.add_parser(
        "scan-m68k-code", help="segue o fluxo 68000 a partir do vetor de reset"
    )
    code_flow.add_argument("--rom", required=True, type=Path)
    code_flow.add_argument("--output", type=Path, default=Path("reports/m68k-code-flow.md"))
    code_flow.add_argument("--entry", type=lambda value: int(value, 0))
    code_flow.add_argument("--max-blocks", type=int, default=5000)

    register_flow = sub.add_parser(
        "scan-m68k-register-flow",
        help="rastreia definições e leituras locais de A0-A3 no código alcançável",
    )
    register_flow.add_argument("--rom", required=True, type=Path)
    register_flow.add_argument(
        "--output", type=Path, default=Path("reports/m68k-register-flow.md")
    )
    register_flow.add_argument("--max-blocks", type=int, default=5000)

    target_inspector = sub.add_parser(
        "inspect-m68k-targets",
        help="inspeciona chamadores e fluxo alcançável de alvos 68000 candidatos",
    )
    target_inspector.add_argument("--rom", required=True, type=Path)
    target_inspector.add_argument(
        "--targets", nargs="+", type=lambda value: int(value, 0), default=list(DEFAULT_TARGETS),
        help="offsets de entrada em decimal ou hexadecimal",
    )
    target_inspector.add_argument(
        "--output", type=Path, default=Path("reports/m68k-target-inspection.md")
    )
    target_inspector.add_argument("--max-blocks-per-target", type=int, default=80)

    overlap = sub.add_parser(
        "audit-m68k-entry-overlaps",
        help="detecta entradas que caem dentro de instruções decodificadas",
    )
    overlap.add_argument("--rom", required=True, type=Path)
    overlap.add_argument(
        "--entries", nargs="+", type=lambda value: int(value, 0),
        default=list(DEFAULT_ENTRIES),
        help="offsets de entrada em decimal ou hexadecimal",
    )
    overlap.add_argument(
        "--output", type=Path, default=Path("reports/m68k-entry-overlaps.md")
    )
    overlap.add_argument("--max-blocks-per-entry", type=int, default=5000)

    indexed = sub.add_parser(
        "scan-indexed-reads",
        help="localiza leituras MOVE.B com endereçamento indexado",
    )
    indexed.add_argument("--rom", required=True, type=Path)
    indexed.add_argument("--output", type=Path, default=Path("reports/m68k-indexed-reads.md"))
    indexed.add_argument("--context", type=lambda value: int(value, 0), default=16)

    japanese = sub.add_parser(
        "scan-japanese-text",
        help="localiza regiões reais de texto japonês Shift-JIS",
    )
    japanese.add_argument("--rom", required=True, type=Path)
    japanese.add_argument(
        "--output", type=Path, default=Path("reports/japanese-text-regions.md")
    )
    japanese.add_argument("--minimum-characters", type=int, default=12)
    japanese.add_argument("--minimum-japanese-ratio", type=float, default=0.65)
    japanese.add_argument("--maximum-region-size", type=lambda value: int(value, 0), default=0x1000)

    return parser


def main() -> int:
    """Executa o comando solicitado e retorna seu código de saída."""
    args = build_parser().parse_args()

    if not args.rom.is_file():
        raise SystemExit(f"ROM não encontrada: {args.rom}")

    if args.command == "scan-japanese-text":
        if args.minimum_characters < 1:
            raise SystemExit("minimum-characters deve ser maior que zero")
        if not 0.0 <= args.minimum_japanese_ratio <= 1.0:
            raise SystemExit("minimum-japanese-ratio deve estar entre 0 e 1")
        if args.maximum_region_size < 1:
            raise SystemExit("maximum-region-size deve ser maior que zero")

        data = args.rom.read_bytes()
        regions = scan_japanese_text(
            data,
            minimum_characters=args.minimum_characters,
            minimum_japanese_ratio=args.minimum_japanese_ratio,
            maximum_region_size=args.maximum_region_size,
        )
        write_japanese_text_report(regions, args.output)
        print(f"Regiões de texto japonês encontradas: {len(regions)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-m68k-code":
        if args.max_blocks < 1:
            raise SystemExit("max-blocks deve ser maior que zero")
        data = args.rom.read_bytes()
        entries = None if args.entry is None else [args.entry]
        blocks = build_control_flow_graph(data, entry_points=entries, max_blocks=args.max_blocks)
        write_code_report(blocks, args.output)
        print(f"Blocos de código alcançáveis: {len(blocks)}")
        print(f"Instruções reconhecidas: {sum(len(block.instructions) for block in blocks)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-m68k-register-flow":
        if args.max_blocks < 1:
            raise SystemExit("max-blocks deve ser maior que zero")
        data = args.rom.read_bytes()
        blocks = build_control_flow_graph(data, max_blocks=args.max_blocks)
        report = trace_register_flow(data, blocks)
        write_register_flow_report(report, args.output)
        print(f"Blocos analisados: {report.blocks}")
        print(f"Definições A0-A3: {len(report.definitions)}")
        print(f"Leituras de byte: {len(report.reads)}")
        print(f"Chamadas JSR: {len(report.calls)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "inspect-m68k-targets":
        if args.max_blocks_per_target < 1:
            raise SystemExit("max-blocks-per-target deve ser maior que zero")
        data = args.rom.read_bytes()
        try:
            write_target_inspection_report(
                data, args.targets, args.output,
                max_blocks_per_target=args.max_blocks_per_target,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(f"Alvos inspecionados: {len(args.targets)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "audit-m68k-entry-overlaps":
        if args.max_blocks_per_entry < 1:
            raise SystemExit("max-blocks-per-entry deve ser maior que zero")
        try:
            overlaps = write_entry_overlap_report(
                args.rom.read_bytes(), args.entries, args.output,
                max_blocks_per_entry=args.max_blocks_per_entry,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(f"Sobreposições encontradas: {len(overlaps)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-indexed-reads":
        if args.context < 0:
            raise SystemExit("context deve ser maior ou igual a zero")
        data = args.rom.read_bytes()
        occurrences = scan_indexed_byte_reads(data, context_size=args.context)
        write_indexed_byte_report(occurrences, args.output)
        print(f"Leituras indexadas encontradas: {len(occurrences)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-reachable-text":
        if args.max_distance < 0:
            raise SystemExit("max-distance deve ser maior ou igual a zero")
        data = args.rom.read_bytes()
        blocks = build_control_flow_graph(data)
        candidates = scan_reachable_text_candidates(
            data, blocks, max_distance=args.max_distance
        )
        write_reachable_text_report(candidates, args.output)
        print(f"Candidatos em blocos alcançáveis: {len(candidates)}")
        print(f"Blocos analisados: {len(blocks)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-a3-flow":
        if args.context < 0:
            raise SystemExit("context deve ser maior ou igual a zero")
        data = args.rom.read_bytes()
        definitions = scan_a3_definitions(data, context_size=args.context)
        uses = scan_a3_byte_reads(data, context_size=args.context)
        write_a3_report(definitions, uses, args.output)
        print(f"Definições de A3 encontradas: {len(definitions)}")
        print(f"Leituras de A3 encontradas: {len(uses)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-text-parser-candidates":
        if args.max_distance < 0 or args.context < 0:
            raise SystemExit("distâncias e contexto devem ser maiores ou iguais a zero")
        data = args.rom.read_bytes()
        candidates = scan_text_parser_candidates(
            data, max_distance=args.max_distance, context_size=args.context
        )
        write_text_parser_report(candidates, args.output)
        print(f"Candidatos encontrados: {len(candidates)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-control-tests":
        if args.context < 0:
            raise SystemExit("context deve ser maior ou igual a zero")
        data = args.rom.read_bytes()
        occurrences = scan_control_tests(data, context_size=args.context)
        write_control_test_report(occurrences, args.output)
        print(f"Comparações encontradas: {len(occurrences)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-refs":
        if args.context < 0:
            raise SystemExit("context deve ser maior ou igual a zero")
        data = args.rom.read_bytes()
        references = scan_known_targets(
            data,
            {"opening_script": 0x01626B, "character_table": 0x1A551A},
            context_size=args.context,
        )
        write_reference_report(references, args.output)
        for name, items in references.items():
            print(f"{name}: {len(items)} referências")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "scan-controls":
        if args.offset < 0 or args.size <= 0:
            raise SystemExit("offset deve ser >= 0 e size deve ser > 0")
        data = args.rom.read_bytes()
        end = args.offset + args.size
        if end > len(data):
            raise SystemExit("a região solicitada ultrapassa o tamanho da ROM")
        occurrences = scan_script_controls(data[args.offset:end], base_offset=args.offset)
        write_control_report(occurrences, args.output)
        print(f"Controles encontrados: {len(occurrences)}")
        print(f"Relatório: {args.output}")
        return 0

    if args.command == "decode-text":
        if args.offset < 0 or args.size <= 0:
            raise SystemExit("offset deve ser >= 0 e size deve ser > 0")
        data = args.rom.read_bytes()
        end = args.offset + args.size
        if end > len(data):
            raise SystemExit("a região solicitada ultrapassa o tamanho da ROM")
        rendered = render_script(
            tokenize_script(
                data[args.offset:end],
                stop_at_terminator=args.stop_at_terminator,
            )
        )
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
