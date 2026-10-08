from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class M68KInstruction:
    """Instrução 68000 reconhecida por um decodificador conservador."""

    offset: int
    size: int
    mnemonic: str
    target: int | None = None

    @property
    def offset_hex(self) -> str:
        return f"0x{self.offset:06X}"


@dataclass(frozen=True)
class CodeBlock:
    """Bloco de código alcançável entre pontos de controle de fluxo."""

    start: int
    end: int
    instructions: tuple[M68KInstruction, ...]
    stopped_reason: str

    @property
    def start_hex(self) -> str:
        return f"0x{self.start:06X}"

    @property
    def end_hex(self) -> str:
        return f"0x{self.end:06X}"


def _word(data: bytes, offset: int) -> int:
    if offset + 2 > len(data):
        raise IndexError
    return int.from_bytes(data[offset : offset + 2], "big")


def _signed8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def _signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def _branch_target(offset: int, displacement: int, size: int) -> int:
    return offset + size + displacement


def decode_instruction(data: bytes, offset: int) -> M68KInstruction | None:
    """Decodifica apenas formas suficientes para construir um CFG inicial.

    O decoder é deliberadamente conservador. Opcode desconhecido retorna None
    em vez de tentar adivinhar o tamanho da instrução.
    """
    if offset < 0 or offset + 2 > len(data) or offset % 2:
        return None

    op = _word(data, offset)

    if op == 0x4E71:
        return M68KInstruction(offset, 2, "NOP")
    if op == 0x4E75:
        return M68KInstruction(offset, 2, "RTS")
    if op == 0x4E73:
        return M68KInstruction(offset, 2, "RTE")
    if op == 0x4E77:
        return M68KInstruction(offset, 2, "RTR")

    # TAS absoluto, presente logo no vetor de inicialização desta ROM.
    if op == 0x4AB9:
        if offset + 6 > len(data):
            return None
        target = int.from_bytes(data[offset + 2 : offset + 6], "big")
        return M68KInstruction(offset, 6, "TAS abs.l", target)
    if op == 0x4A79:
        if offset + 4 > len(data):
            return None
        target = int.from_bytes(data[offset + 2 : offset + 4], "big")
        return M68KInstruction(offset, 4, "TAS abs.w", target)

    if (op & 0xF000) == 0x6000:
        condition = (op >> 8) & 0xF
        displacement8 = op & 0xFF
        if displacement8 == 0:
            if offset + 4 > len(data):
                return None
            displacement = _signed16(_word(data, offset + 2))
            size = 4
        elif displacement8 == 0xFF:
            return None
        else:
            displacement = _signed8(displacement8)
            size = 2
        target = _branch_target(offset, displacement, size)
        names = {
            0: "BRA", 1: "BSR", 2: "BHI", 3: "BLS",
            4: "BCC", 5: "BCS", 6: "BNE", 7: "BEQ",
            8: "BVC", 9: "BVS", 10: "BPL", 11: "BMI",
            12: "BGE", 13: "BLT", 14: "BGT", 15: "BLE",
        }
        return M68KInstruction(offset, size, names[condition], target)

    if op in (0x4EF9, 0x4EB9):
        if offset + 6 > len(data):
            return None
        target = int.from_bytes(data[offset + 2 : offset + 6], "big")
        mnemonic = "JMP abs.l" if op == 0x4EF9 else "JSR abs.l"
        return M68KInstruction(offset, 6, mnemonic, target)

    if op in (0x41F9, 0x4879):
        if offset + 6 > len(data):
            return None
        target = int.from_bytes(data[offset + 2 : offset + 6], "big")
        mnemonic = "LEA abs.l" if op == 0x41F9 else "PEA abs.l"
        return M68KInstruction(offset, 6, mnemonic, target)

    if (op & 0xF100) == 0x7000:
        return M68KInstruction(offset, 2, "MOVEQ")

    if (op & 0xF1F8) == 0x1018:
        return M68KInstruction(offset, 2, "MOVE.B (An)+,Dn")

    if (op & 0xF1F8) == 0x1010:
        return M68KInstruction(offset, 2, "MOVE.B (An),Dn")

    if (op & 0x0038) == 0x0030 and (op >> 12) == 0x1:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "MOVE.B (An,Dn.W/L),Dm")

    if (op & 0xF1C0) == 0x2640:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "MOVEA.L d16(An),A3")

    if (op & 0xF1C0) == 0x3640:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "MOVEA.W d16(An),A3")

    if (op & 0xF1C0) == 0x41C0:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "LEA d16(An),An")

    if (op & 0xFF00) == 0x0C00:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "CMPI.B #imm,Dn")

    if (op & 0xFFC0) == 0x0C40:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "CMPI.W #imm,Dn")

    return None


def reset_vector(data: bytes) -> int:
    """Retorna o PC inicial do vetor 68000 da ROM Mega Drive."""
    if len(data) < 8:
        raise ValueError("ROM pequena demais para o vetor de reset")
    target = int.from_bytes(data[4:8], "big")
    if target % 2 or target >= len(data):
        raise ValueError("vetor de reset fora da ROM ou desalinhado")
    return target


def build_control_flow_graph(
    data: bytes,
    *,
    entry_points: list[int] | None = None,
    max_blocks: int = 5000,
) -> list[CodeBlock]:
    """Constrói um CFG inicial seguindo apenas instruções reconhecidas."""
    if max_blocks < 1:
        raise ValueError("max_blocks deve ser maior que zero")

    entries = list(entry_points) if entry_points is not None else [reset_vector(data)]
    pending = list(dict.fromkeys(entries))
    visited: set[int] = set()
    blocks: list[CodeBlock] = []

    while pending and len(blocks) < max_blocks:
        start = pending.pop()
        if start in visited or start < 0 or start >= len(data) or start % 2:
            continue
        visited.add(start)

        instructions: list[M68KInstruction] = []
        offset = start
        reason = "unknown_opcode"

        while offset < len(data):
            instruction = decode_instruction(data, offset)
            if instruction is None:
                reason = "unknown_opcode"
                break

            instructions.append(instruction)
            next_offset = offset + instruction.size

            if instruction.mnemonic in {"RTS", "RTE", "RTR"}:
                reason = "return"
                offset = next_offset
                break

            if instruction.mnemonic == "JMP abs.l":
                if instruction.target is not None:
                    pending.append(instruction.target)
                reason = "jump"
                offset = next_offset
                break

            if instruction.mnemonic == "JSR abs.l":
                pending.append(instruction.target)
                offset = next_offset
                continue

            if instruction.mnemonic == "BRA":
                pending.append(instruction.target)
                reason = "branch"
                offset = next_offset
                break

            if instruction.mnemonic == "BSR":
                pending.append(instruction.target)
                offset = next_offset
                continue

            if instruction.mnemonic.startswith("B") and instruction.mnemonic not in {"BRA", "BSR"}:
                pending.append(instruction.target)
                if next_offset < len(data):
                    pending.append(next_offset)
                reason = "conditional_branch"
                offset = next_offset
                break

            offset = next_offset

        if instructions:
            blocks.append(CodeBlock(start, offset, tuple(instructions), reason))

    return sorted(blocks, key=lambda block: block.start)


def write_code_report(blocks: list[CodeBlock], output) -> None:
    """Escreve relatório Markdown do CFG inicial."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    instruction_count = sum(len(block.instructions) for block in blocks)
    lines = [
        "# M68K code-flow report",
        "",
        "> CFG inicial conservador; opcode desconhecido encerra o bloco.",
        "> Não é um desassemblador completo e não prova que todo bloco é código.",
        "",
        f"- Blocos: {len(blocks)}",
        f"- Instruções reconhecidas: {instruction_count}",
        "",
        "## Blocos",
        "",
        "| Início | Fim | Instruções | Parada |",
        "|---:|---:|---:|---|",
    ]

    for block in blocks:
        lines.append(
            f"| {block.start_hex} | {block.end_hex} | "
            f"{len(block.instructions)} | {block.stopped_reason} |"
        )

    lines.extend(["", "## Chamadas e acessos relevantes", ""])
    for block in blocks:
        for instruction in block.instructions:
            if instruction.mnemonic in {
                "JSR abs.l",
                "JMP abs.l",
                "MOVE.B (An)+,Dn",
                "MOVE.B (An),Dn",
                "MOVE.B (An,Dn.W/L),Dm",
                "CMPI.B #imm,Dn",
            }:
                target = (
                    f" -> 0x{instruction.target:06X}"
                    if instruction.target is not None
                    else ""
                )
                lines.append(
                    f"- {instruction.offset_hex} {instruction.mnemonic}{target}"
                )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
