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


def _ea_extension_size(mode: int, register: int, operand_size: int, *, source: bool) -> int | None:
    """Retorna o tamanho da extensão do effective address em bytes."""
    if mode <= 4:
        return 0
    if mode in (5, 6):
        return 2
    if mode == 7:
        if register == 0:
            return 2
        if register == 1:
            return 4
        if source and register == 4:
            # O campo imediato do 68000 ocupa uma extensão de 16 bits
            # para BYTE/WORD e 32 bits para LONG.
            return 4 if operand_size == 4 else 2
    return None


def _decode_move(data: bytes, offset: int, op: int) -> M68KInstruction | None:
    """Decodifica MOVE/MOVEA nas formas gerais do 68000."""
    top = op >> 12
    if top not in (1, 2, 3):
        return None

    operand_size = 1 if top == 1 else 2 if top == 3 else 4
    source_mode = (op >> 3) & 0x7
    source_register = op & 0x7
    destination_mode = (op >> 6) & 0x7

    # MOVEA usa destino An e apenas tamanhos W/L.
    if destination_mode == 1 and top in (2, 3):
        source_extension = _ea_extension_size(
            source_mode, source_register, operand_size, source=True
        )
        if source_extension is None:
            return None
        return M68KInstruction(
            offset,
            2 + source_extension,
            "MOVEA.L" if top == 2 else "MOVEA.W",
        )

    destination_extension = _ea_extension_size(
        destination_mode, (op >> 9) & 0x7, operand_size, source=False
    )
    source_extension = _ea_extension_size(
        source_mode, source_register, operand_size, source=True
    )
    if destination_extension is None or source_extension is None:
        return None

    size_name = {1: "MOVE.B", 2: "MOVE.L", 3: "MOVE.W"}[top]
    source_name = {
        0: "Dn",
        2: "(An)",
        3: "(An)+",
        4: "-(An)",
        5: "d16(An)",
        6: "d8(An,Xn)",
        7: "xxx",
    }.get(source_mode)
    destination_name = {
        0: "Dn",
        2: "(An)",
        3: "(An)+",
        4: "-(An)",
        5: "d16(An)",
        6: "d8(An,Xn)",
        7: "xxx",
    }.get(destination_mode)

    mnemonic = size_name
    if source_name is not None and destination_name is not None:
        if source_mode == 7 and source_register == 4:
            source_name = "#imm"
        elif source_mode == 7 and source_register == 0:
            source_name = "(xxx).W"
        elif source_mode == 7 and source_register == 1:
            source_name = "(xxx).L"
        mnemonic = f"{size_name} {source_name},{destination_name}"

    target = None
    if destination_mode == 7 and (op >> 9) & 0x7 == 0 and (op & 0x3F) == 0x39:
        target = int.from_bytes(data[offset + 2 + source_extension:offset + 4 + source_extension], "big")
    return M68KInstruction(
        offset,
        2 + source_extension + destination_extension,
        mnemonic,
        target,
    )


def decode_instruction(data: bytes, offset: int) -> M68KInstruction | None:
    """Decodifica formas 68000 suficientes para construir um CFG inicial.

    O decoder continua conservador: uma forma não reconhecida retorna None.
    O objetivo é preservar o alinhamento do fluxo, não substituir um
    desassembler completo.
    """
    if offset < 0 or offset + 2 > len(data) or offset % 2:
        return None

    op = _word(data, offset)

    # Instruções de controle/sistema que aparecem no bootstrap.
    # Elas não introduzem novos destinos no CFG, mas precisam consumir
    # exatamente o tamanho correto para manter o alinhamento.
    if 0x4E60 <= op <= 0x4E67:
        return M68KInstruction(offset, 2, "MOVE USP,An")
    if 0x4E68 <= op <= 0x4E6F:
        return M68KInstruction(offset, 2, "MOVE An,USP")
    if (op & 0xFFF8) == 0x4E40:
        return M68KInstruction(offset, 2, "TRAP")
    if op == 0x4E72:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "STOP")
    if op == 0x4E74:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "RTD")
    if op == 0x4E7A or op == 0x4E7B:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "MOVEC")
    if (op & 0xFFF8) == 0x4E50:
        if offset + 2 > len(data):
            return None
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "LINK")
    if (op & 0xFFF8) == 0x4E58:
        return M68KInstruction(offset, 2, "UNLK")
    if (op & 0xFFC0) == 0x46C0:
        extension = _ea_extension_size((op >> 3) & 0x7, op & 0x7, 2, source=True)
        if extension is None:
            return None
        return M68KInstruction(offset, 2 + extension, "MOVE.W <EA>,SR")
    if (op & 0xFFC0) == 0x44C0:
        extension = _ea_extension_size((op >> 3) & 0x7, op & 0x7, 2, source=True)
        if extension is None:
            return None
        return M68KInstruction(offset, 2 + extension, "MOVE.W <EA>,CCR")
    # NEGX.B/W/L <EA>: complemento com extensão (68000).
    # As formas imediatas não são válidas para esta instrução.
    if (op & 0xFFC0) in (0x4000, 0x4040, 0x4080):
        mode = (op >> 3) & 0x7
        register = op & 0x7
        size = {0x4000: 1, 0x4040: 2, 0x4080: 4}[op & 0xFFC0]
        if mode == 1 or (mode == 7 and register not in (0, 1)):
            return None
        extension = _ea_extension_size(mode, register, size, source=False)
        if extension is None:
            return None
        suffix = {1: "B", 2: "W", 4: "L"}[size]
        return M68KInstruction(
            offset,
            2 + extension,
            f"NEGX.{suffix} <EA>",
        )

    if (op & 0xFFC0) == 0x40C0:
        mode = (op >> 3) & 0x7
        register = op & 0x7
        if mode == 1 or (mode == 7 and register not in (0, 1)):
            return None
        extension = _ea_extension_size(mode, register, 2, source=False)
        if extension is None:
            return None
        return M68KInstruction(offset, 2 + extension, "MOVE.W SR,<EA>")


    if op == 0x4E71:
        return M68KInstruction(offset, 2, "NOP")
    if op == 0x4E75:
        return M68KInstruction(offset, 2, "RTS")
    if op == 0x4E73:
        return M68KInstruction(offset, 2, "RTE")
    if op == 0x4E77:
        return M68KInstruction(offset, 2, "RTR")

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

    if (op & 0xFFF8) == 0x4ED0:
        return M68KInstruction(offset, 2, "JMP (An)")
    if (op & 0xFFF8) == 0x4E90:
        return M68KInstruction(offset, 2, "JSR (An)")

    # LEA abs.l: bits 11-9 selecionam o registrador A0-A7.
    # A forma base 41F9 corresponde a LEA $xxxxxxxx,A0.
    if (op & 0xF1FF) == 0x41F9:
        if offset + 6 > len(data):
            return None
        target = int.from_bytes(data[offset + 2 : offset + 6], "big")
        register = (op >> 9) & 0x7
        return M68KInstruction(offset, 6, f"LEA abs.l,A{register}", target)

    if op == 0x4879:
        if offset + 6 > len(data):
            return None
        target = int.from_bytes(data[offset + 2 : offset + 6], "big")
        return M68KInstruction(offset, 6, "PEA abs.l", target)

    if (op & 0xF1FF) == 0x41FA:
        if offset + 4 > len(data):
            return None
        displacement = _signed16(_word(data, offset + 2))
        target = offset + 4 + displacement
        return M68KInstruction(offset, 4, "LEA d16(PC),An", target)

    if (op & 0xF1C0) == 0x41C0:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "LEA d16(An),An")

    if (op & 0xFB80) in (0x4880, 0x4C80):
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "MOVEM")

    if (op & 0xF0F8) == 0x50C8:
        if offset + 4 > len(data):
            return None
        displacement = _signed16(_word(data, offset + 2))
        target = offset + 4 + displacement
        return M68KInstruction(offset, 4, "DBcc", target)

    if (op & 0xF100) in (0x5000, 0x5100):
        return M68KInstruction(offset, 2, "ADDQ/SUBQ")

    if (op & 0xF000) == 0xE000:
        return M68KInstruction(offset, 2, "SHIFT/ROTATE")

    # BTST/BCHG/BCLR/BSET dinâmico.
    if (op & 0xF100) == 0x0100:
        return M68KInstruction(offset, 2, "BIT dynamic")

    # Bit operation with immediate bit number. The extension word carries
    # the bit number, so the instruction occupies four bytes.
    if (op & 0xFFC0) == 0x0800:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "BTST #imm,<EA>")

    if (op & 0xFF00) == 0x0C00:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "CMPI.B #imm,Dn")

    # ANDI/ORI/SUBI/ADDI byte.
    if (op & 0xFF00) in (0x0000, 0x0200, 0x0400, 0x0600, 0x0A00):
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "IMMEDIATE.B")

    # MOVEQ #imm,Dn.
    if (op & 0xF100) == 0x7000:
        return M68KInstruction(offset, 2, "MOVEQ")

    # ADDA/SUBA.W/L, incluindo operando imediato. O modo de EA e o
    # tamanho da extensão precisam ser respeitados para manter o alinhamento.
    if (op & 0xF000) in (0x9000, 0xD000) and ((op >> 6) & 0x7) in (3, 7):
        source_mode = (op >> 3) & 0x7
        source_register = op & 0x7
        operand_size = 4 if ((op >> 6) & 0x7) == 7 else 2
        extension = _ea_extension_size(
            source_mode, source_register, operand_size, source=True
        )
        if extension is None:
            return None
        operation = "ADDA" if (op & 0xF000) == 0xD000 else "SUBA"
        size_name = "L" if operand_size == 4 else "W"
        return M68KInstruction(offset, 2 + extension, f"{operation}.{size_name}")

    # Todas as formas gerais de MOVE/MOVEA.
    move = _decode_move(data, offset, op)
    if move is not None:
        return move

    # ADD/SUB/CMP register-to-EA nas formas de uma palavra sem extensão.
    if (op & 0xF000) in (0x9000, 0xB000, 0xD000):
        mode = (op >> 3) & 0x7
        register = op & 0x7
        if _ea_extension_size(mode, register, 2, source=False) is not None:
            return M68KInstruction(offset, 2, "ARITHMETIC")

    if op == 0x46FC:
        if offset + 4 > len(data):
            return None
        return M68KInstruction(offset, 4, "MOVE.W #imm,SR")

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
    """Constrói um CFG conservador com blocos básicos não sobrepostos.

    A primeira etapa descobre instruções alcançáveis e seus sucessores. A
    segunda transforma os pontos de entrada e destinos de controle em
    fronteiras de blocos. Isso evita que um branch que aponte para o meio de
    um bloco produza blocos sobrepostos.
    """
    if max_blocks < 1:
        raise ValueError("max_blocks deve ser maior que zero")

    entries = list(entry_points) if entry_points is not None else [reset_vector(data)]
    pending = list(dict.fromkeys(entries))
    instructions: dict[int, M68KInstruction] = {}
    leaders: set[int] = set()
    visited: set[int] = set()

    while pending:
        start = pending.pop()
        if start is None or start in visited:
            continue
        if start < 0 or start >= len(data) or start % 2:
            continue

        visited.add(start)
        leaders.add(start)
        offset = start

        while offset < len(data):
            if offset in instructions:
                break

            instruction = decode_instruction(data, offset)
            if instruction is None:
                break

            instructions[offset] = instruction
            next_offset = offset + instruction.size

            if instruction.mnemonic in {"RTS", "RTE", "RTR"}:
                break

            if instruction.mnemonic in {"JMP abs.l", "JMP (An)"}:
                if instruction.target is not None:
                    leaders.add(instruction.target)
                    pending.append(instruction.target)
                break

            if instruction.mnemonic in {"JSR abs.l", "JSR (An)"}:
                if instruction.target is not None:
                    leaders.add(instruction.target)
                    pending.append(instruction.target)
                if next_offset < len(data):
                    leaders.add(next_offset)
                offset = next_offset
                continue

            if instruction.mnemonic == "BRA":
                if instruction.target is not None:
                    leaders.add(instruction.target)
                    pending.append(instruction.target)
                break

            if instruction.mnemonic == "BSR":
                if instruction.target is not None:
                    leaders.add(instruction.target)
                    pending.append(instruction.target)
                if next_offset < len(data):
                    leaders.add(next_offset)
                offset = next_offset
                continue

            if instruction.mnemonic.startswith("B") and instruction.mnemonic not in {
                "BRA",
                "BSR",
            }:
                if instruction.target is not None:
                    leaders.add(instruction.target)
                    pending.append(instruction.target)
                if next_offset < len(data):
                    leaders.add(next_offset)
                    pending.append(next_offset)
                break

            offset = next_offset

    blocks: list[CodeBlock] = []
    for start in sorted(leaders):
        if len(blocks) >= max_blocks:
            break

        instruction = instructions.get(start)
        if instruction is None:
            continue

        block_instructions: list[M68KInstruction] = []
        offset = start
        reason = "unknown_opcode"

        while offset in instructions:
            if offset != start and offset in leaders:
                reason = "block_boundary"
                break

            current = instructions[offset]
            block_instructions.append(current)
            next_offset = offset + current.size

            if current.mnemonic in {"RTS", "RTE", "RTR"}:
                reason = "return"
                offset = next_offset
                break

            if current.mnemonic in {"JMP abs.l", "JMP (An)"}:
                reason = "jump" if current.mnemonic == "JMP abs.l" else "indirect_jump"
                offset = next_offset
                break

            if current.mnemonic == "BRA":
                reason = "branch"
                offset = next_offset
                break

            if current.mnemonic == "BSR":
                # BSR é uma chamada com retorno: o destino entra no CFG,
                # mas a execução sequencial continua após a instrução.
                offset = next_offset
                continue

            if current.mnemonic.startswith("B"):
                reason = "conditional_branch"
                offset = next_offset
                break

            if current.mnemonic in {"JSR abs.l", "JSR (An)"}:
                offset = next_offset
                continue

            offset = next_offset

        if block_instructions:
            blocks.append(
                CodeBlock(
                    start=start,
                    end=offset,
                    instructions=tuple(block_instructions),
                    stopped_reason=reason,
                )
            )

    return blocks


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
