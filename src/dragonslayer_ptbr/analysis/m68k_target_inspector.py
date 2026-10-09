from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .m68k_code import CodeBlock, M68KInstruction, build_control_flow_graph

DEFAULT_TARGETS = (0x001D1E, 0x001EC0, 0x00D8F0)


def _format_instruction(data: bytes, instruction: M68KInstruction) -> str:
    raw = data[instruction.offset : instruction.offset + instruction.size].hex(" ").upper()
    target = "" if instruction.target is None else f" -> 0x{instruction.target:06X}"
    return f"`0x{instruction.offset:06X}`  `{raw:<23}`  {instruction.mnemonic}{target}"


def inspect_targets(
    data: bytes,
    targets: Sequence[int] = DEFAULT_TARGETS,
    *,
    max_blocks_per_target: int = 80,
) -> str:
    """Gera relatório dos chamadores alcançáveis e dos fluxos a partir dos alvos.

    A análise do chamador parte do vetor de reset. Cada alvo também é usado
    como ponto de entrada independente, para permitir inspecioná-lo mesmo
    quando o CFG principal não o alcançou. Isso não prova que o alvo seja
    código executado em runtime.
    """
    if max_blocks_per_target < 1:
        raise ValueError("max_blocks_per_target deve ser maior que zero")
    normalized = tuple(dict.fromkeys(targets))
    for target in normalized:
        if target < 0 or target >= len(data) or target % 2:
            raise ValueError(f"alvo inválido ou desalinhado: 0x{target:X}")

    main_blocks = build_control_flow_graph(data)
    caller_map: dict[int, list[tuple[CodeBlock, M68KInstruction]]] = {
        target: [] for target in normalized
    }
    for block in main_blocks:
        for instruction in block.instructions:
            if instruction.mnemonic in {"JSR abs.l", "BSR"} and instruction.target in caller_map:
                caller_map[instruction.target].append((block, instruction))

    lines = [
        "# Inspeção de alvos 68000",
        "",
        "> Relatório estático exploratório. Instruções desconhecidas interrompem o bloco; "
        "um alvo forçado como entrada não comprova execução em runtime.",
        "",
        f"- Blocos alcançados a partir do vetor de reset: {len(main_blocks)}",
        f"- Alvos solicitados: {len(normalized)}",
        "",
    ]

    for target in normalized:
        lines.extend([f"## Alvo 0x{target:06X}", "", "### Chamadores encontrados no CFG do reset", ""])
        callers = caller_map[target]
        if not callers:
            lines.append("Nenhuma chamada direta reconhecida no CFG do reset.")
        else:
            for block, instruction in callers:
                lines.append(
                    f"- Bloco `0x{block.start:06X}`–`0x{block.end:06X}`, "
                    f"chamada em `0x{instruction.offset:06X}`."
                )
                for item in block.instructions:
                    lines.append(f"  - {_format_instruction(data, item)}")

        lines.extend(["", "### Fluxo alcançável a partir do alvo", ""])
        target_blocks = build_control_flow_graph(
            data, entry_points=[target], max_blocks=max_blocks_per_target
        )
        if not target_blocks:
            lines.append("O decoder conservador não reconheceu uma instrução válida neste offset.")
            lines.append("")
            continue

        lines.append(
            f"Blocos decodificados: {len(target_blocks)} "
            f"(limite configurado: {max_blocks_per_target})."
        )
        lines.append("")
        for block in target_blocks:
            lines.append(
                f"#### Bloco `0x{block.start:06X}`–`0x{block.end:06X}` "
                f"({block.stopped_reason})"
            )
            lines.append("")
            for instruction in block.instructions:
                lines.append(f"- {_format_instruction(data, instruction)}")
            lines.append("")

    lines.extend([
        "## Como interpretar",
        "",
        "- Chamadores listados são apenas chamadas diretas reconhecidas no CFG do reset.",
        "- Chamadas indiretas `JSR (An)` não têm destino estático resolvido por esta ferramenta.",
        "- O fluxo iniciado artificialmente em cada alvo é útil para inspeção, mas pode entrar em dados.",
        "- A classificação como parser exige evidência adicional de ponteiro de script, controles e renderização.",
        "",
    ])
    return "\n".join(lines)


def write_target_inspection_report(
    data: bytes,
    targets: Sequence[int],
    output: str | Path,
    *,
    max_blocks_per_target: int = 80,
) -> None:
    """Escreve o relatório de inspeção de alvos em Markdown."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        inspect_targets(data, targets, max_blocks_per_target=max_blocks_per_target),
        encoding="utf-8",
    )
