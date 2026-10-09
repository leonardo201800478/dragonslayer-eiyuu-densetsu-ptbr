from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .m68k_code import M68KInstruction, build_control_flow_graph


DEFAULT_ENTRIES = (0x01E9AC, 0x01E9C0, 0x0262C4, 0x02AF20, 0x02AF80, 0x02AF90, 0x02AF94)


@dataclass(frozen=True)
class EntryOverlap:
    """Ponto de entrada que cai dentro de outra instrução decodificada."""

    entry_point: int
    instruction_offset: int
    instruction_end: int
    instruction_mnemonic: str
    instruction_bytes: bytes
    source_entry: int


def find_entry_overlaps(
    data: bytes,
    entry_points: Sequence[int] = DEFAULT_ENTRIES,
    *,
    max_blocks_per_entry: int = 5000,
) -> tuple[EntryOverlap, ...]:
    """Compara CFGs independentes e identifica entradas no interior de instruções.

    Uma sobreposição pode indicar fluxo sobreposto, dados interpretados como
    código, entrada incorreta ou erro do decoder. O achado não determina qual
    interpretação está correta e não prova execução em runtime.
    """
    if max_blocks_per_entry < 1:
        raise ValueError("max_blocks_per_entry deve ser maior que zero")
    entries = tuple(dict.fromkeys(entry_points))
    if not entries:
        raise ValueError("informe ao menos um ponto de entrada")

    analyses: dict[int, dict[int, M68KInstruction]] = {}
    for entry in entries:
        if entry < 0 or entry >= len(data) or entry % 2:
            raise ValueError(f"entrada inválida ou desalinhada: 0x{entry:X}")
        blocks = build_control_flow_graph(
            data, entry_points=[entry], max_blocks=max_blocks_per_entry
        )
        analyses[entry] = {
            instruction.offset: instruction
            for block in blocks
            for instruction in block.instructions
        }

    overlaps: set[EntryOverlap] = set()
    for source_entry, instructions in analyses.items():
        for instruction in instructions.values():
            end = instruction.offset + instruction.size
            for candidate in entries:
                if candidate != source_entry and instruction.offset < candidate < end:
                    overlaps.add(
                        EntryOverlap(
                            candidate, instruction.offset, end,
                            instruction.mnemonic,
                            data[instruction.offset:end],
                            source_entry,
                        )
                    )
    return tuple(sorted(overlaps, key=lambda item: (
        item.entry_point, item.instruction_offset, item.source_entry
    )))


def render_entry_overlap_report(
    entry_points: Sequence[int],
    overlaps: Sequence[EntryOverlap],
) -> str:
    lines = [
        "# Auditoria de sobreposição de entradas 68000",
        "",
        "> Análise estática exploratória. Uma sobreposição sinaliza interpretações incompatíveis; não prova qual fluxo é executado em runtime.",
        "",
        "## Entradas analisadas",
        "",
    ]
    lines.extend(f"- `0x{entry:06X}`" for entry in entry_points)
    lines.extend(["", "## Sobreposições encontradas", ""])
    if not overlaps:
        lines.append("Nenhuma sobreposição entre as entradas analisadas e instruções reconhecidas.")
    else:
        lines.extend([
            "| Entrada dentro da instrução | Instrução decodificada | Origem da análise |",
            "|---:|---|---:|",
        ])
        for item in overlaps:
            lines.append(
                f"| `0x{item.entry_point:06X}` | "
                f"`0x{item.instruction_offset:06X}–0x{item.instruction_end:06X}` "
                f"(`{item.instruction_mnemonic}`) | "
                f"`{item.instruction_bytes.hex(\" \").upper()}` | `0x{item.source_entry:06X}` |"
            )
    lines.extend([
        "",
        "## Interpretação",
        "",
        "- Uma entrada dentro dos bytes de outra instrução pode indicar código sobreposto, dados interpretados como instruções, entrada incorreta ou erro do decoder.",
        "- O resultado não confirma parser de texto nem execução em runtime.",
        "- Compare os bytes com um segundo disassembler 68000 e valide a origem das chamadas antes de classificar qualquer candidato.",
        "",
    ])
    return "\n".join(lines) + "\n"


def write_entry_overlap_report(
    data: bytes,
    entry_points: Sequence[int],
    output,
    *,
    max_blocks_per_entry: int = 5000,
) -> tuple[EntryOverlap, ...]:
    from pathlib import Path

    overlaps = find_entry_overlaps(
        data, entry_points, max_blocks_per_entry=max_blocks_per_entry
    )
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_entry_overlap_report(entry_points, overlaps), encoding="utf-8")
    return overlaps
