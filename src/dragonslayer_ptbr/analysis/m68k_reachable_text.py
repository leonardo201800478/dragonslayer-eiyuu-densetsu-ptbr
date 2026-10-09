from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .m68k_code import CodeBlock, build_control_flow_graph


@dataclass(frozen=True)
class ReachableTextCandidate:
    """Leitura de byte seguida de teste de controle no mesmo bloco alcançável."""

    block_start: int
    read_offset: int
    test_offset: int
    address_register: int
    data_register: int
    control: int

    @property
    def control_hex(self) -> str:
        return f"0x{self.control:02X}"


def scan_reachable_text_candidates(
    data: bytes,
    blocks: list[CodeBlock] | None = None,
    *,
    controls: tuple[int, ...] = (0x01, 0x06, 0x0E, 0x00),
    max_distance: int = 16,
) -> list[ReachableTextCandidate]:
    """Cruza MOVE.B (An)+,Dn e CMPI.B #controle,Dn no CFG alcançável.

    Ao contrário do scanner binário amplo, só considera offsets reconhecidos
    como instruções em blocos do CFG. A associação permanece heurística:
    o decoder é parcial, e o CFG pode conter blocos que coincidem com dados.
    """
    if max_distance < 0:
        raise ValueError("max_distance deve ser maior ou igual a zero")
    if any(not 0 <= value <= 0xFF for value in controls):
        raise ValueError("controls deve conter bytes entre 0 e 255")

    reachable_blocks = blocks if blocks is not None else build_control_flow_graph(data)
    allowed = set(controls)
    candidates: list[ReachableTextCandidate] = []

    for block in reachable_blocks:
        instructions = block.instructions
        for index, instruction in enumerate(instructions):
            if instruction.size < 2 or instruction.offset + 2 > len(data):
                continue
            opcode = int.from_bytes(data[instruction.offset : instruction.offset + 2], "big")

            # MOVE.B (An)+,Dn: top nibble 1, source mode 3.
            if (opcode & 0xF1F8) != 0x1018:
                continue

            address_register = opcode & 0x7
            data_register = (opcode >> 9) & 0x7
            for test in instructions[index + 1 :]:
                distance = test.offset - instruction.offset
                if distance > max_distance:
                    break
                if distance < 2 or test.offset + 4 > len(data):
                    continue
                test_opcode = int.from_bytes(data[test.offset : test.offset + 2], "big")
                if (test_opcode & 0xFFF8) != 0x0C00:
                    continue
                if (test_opcode & 0x7) != data_register:
                    continue
                if data[test.offset + 2] != 0:
                    continue
                control = data[test.offset + 3]
                if control not in allowed:
                    continue

                candidates.append(
                    ReachableTextCandidate(
                        block_start=block.start,
                        read_offset=instruction.offset,
                        test_offset=test.offset,
                        address_register=address_register,
                        data_register=data_register,
                        control=control,
                    )
                )
                break

    return candidates


def write_reachable_text_report(
    candidates: list[ReachableTextCandidate],
    output: str | Path,
) -> None:
    """Escreve relatório Markdown dos candidatos no CFG alcançável."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Candidatos a parser de texto no CFG alcançável",
        "",
        "> Evidência estática exploratória; não confirma semântica nem execução real.",
        "",
        f"Total: {len(candidates)}",
        "",
        "| Bloco | Leitura | Teste | Ponteiro | Registrador | Controle |",
        "|---:|---:|---:|---|---|---:|",
    ]
    for item in candidates:
        lines.append(
            f"| 0x{item.block_start:06X} | 0x{item.read_offset:06X} | "
            f"0x{item.test_offset:06X} | A{item.address_register} | "
            f"D{item.data_register} | {item.control_hex} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
