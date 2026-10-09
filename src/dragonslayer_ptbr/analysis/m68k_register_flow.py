from __future__ import annotations

from dataclasses import dataclass

from .m68k_code import CodeBlock, M68KInstruction


@dataclass(frozen=True)
class RegisterDefinition:
    """Definição de A0-A3 dentro de um bloco alcançável."""

    offset: int
    register: int
    kind: str
    value: int | None = None

    @property
    def offset_hex(self) -> str:
        """Retorna o offset em hexadecimal."""
        return f"0x{self.offset:06X}"


@dataclass(frozen=True)
class RegisterRead:
    """Leitura de byte através de A0-A3."""

    offset: int
    address_register: int
    data_register: int
    mode: str
    definition_offset: int | None
    definition_value: int | None

    @property
    def offset_hex(self) -> str:
        """Retorna o offset em hexadecimal."""
        return f"0x{self.offset:06X}"


@dataclass(frozen=True)
class RegisterFlowReport:
    """Resultado do rastreamento local de A0-A3."""

    blocks: int
    definitions: tuple[RegisterDefinition, ...]
    reads: tuple[RegisterRead, ...]
    calls: tuple[M68KInstruction, ...]


def _constant_definition(
    data: bytes, instruction: M68KInstruction
) -> tuple[int, int, str] | None:
    """Extrai definições constantes de A0-A3."""
    offset = instruction.offset
    if offset + 2 > len(data):
        return None
    op = int.from_bytes(data[offset : offset + 2], "big")

    if (op & 0xF1FF) == 0x41F9 and offset + 6 <= len(data):
        register = (op >> 9) & 7
        value = int.from_bytes(data[offset + 2 : offset + 6], "big")
        return register, value, "LEA abs.l"

    if (op & 0xF1FF) == 0x41FA and offset + 4 <= len(data):
        register = (op >> 9) & 7
        displacement = int.from_bytes(data[offset + 2 : offset + 4], "big", signed=True)
        return register, offset + 4 + displacement, "LEA d16(PC)"

    top = op >> 12
    if top in (2, 3) and ((op >> 6) & 7) == 1 and ((op >> 3) & 7) == 7 and (op & 7) == 4:
        register = (op >> 9) & 7
        size = 4 if top == 2 else 2
        if offset + 2 + size > len(data):
            return None
        value = int.from_bytes(data[offset + 2 : offset + 2 + size], "big")
        return register, value, "MOVEA.L #imm" if top == 2 else "MOVEA.W #imm"

    return None


def _movea_destination(data: bytes, instruction: M68KInstruction) -> int | None:
    """Retorna o destino A0-A3 de MOVEA.L/W."""
    op = int.from_bytes(data[instruction.offset : instruction.offset + 2], "big")
    if (op >> 12) not in (2, 3) or ((op >> 6) & 7) != 1:
        return None
    register = (op >> 9) & 7
    return register if register <= 3 else None


def _byte_read(data: bytes, instruction: M68KInstruction) -> tuple[int, int, str] | None:
    """Extrai MOVE.B (An) ou MOVE.B (An)+ para A0-A3."""
    op = int.from_bytes(data[instruction.offset : instruction.offset + 2], "big")
    if (op >> 12) != 1:
        return None
    mode = (op >> 3) & 7
    address_register = op & 7
    if mode not in (2, 3) or address_register > 3:
        return None
    return address_register, (op >> 9) & 7, "(An)" if mode == 2 else "(An)+"


def trace_register_flow(
    data: bytes,
    blocks: list[CodeBlock],
    *,
    registers: tuple[int, ...] = (0, 1, 2, 3),
) -> RegisterFlowReport:
    """Rastreia A0-A3 somente dentro de cada bloco alcançável.

    Nenhuma origem é propagada através de uma fronteira de bloco ou chamada
    JSR, evitando inferências interprocedurais sem evidência.
    """
    if any(register < 0 or register > 3 for register in registers):
        raise ValueError("registers deve conter somente A0-A3")

    definitions: list[RegisterDefinition] = []
    reads: list[RegisterRead] = []
    calls: list[M68KInstruction] = []

    for block in blocks:
        current: dict[int, RegisterDefinition] = {}
        for instruction in block.instructions:
            if instruction.mnemonic.startswith("JSR"):
                calls.append(instruction)
                current.clear()

            constant = _constant_definition(data, instruction)
            if constant is not None:
                register, value, kind = constant
                if register in registers:
                    item = RegisterDefinition(instruction.offset, register, kind, value)
                    definitions.append(item)
                    current[register] = item
                continue

            destination = _movea_destination(data, instruction)
            if destination is not None and destination in registers:
                current.pop(destination, None)
                definitions.append(
                    RegisterDefinition(instruction.offset, destination, "MOVEA.L/W <EA>")
                )
                continue

            byte_read = _byte_read(data, instruction)
            if byte_read is None:
                continue

            address_register, data_register, mode = byte_read
            origin = current.get(address_register)
            reads.append(
                RegisterRead(
                    instruction.offset,
                    address_register,
                    data_register,
                    mode,
                    origin.offset if origin else None,
                    origin.value if origin else None,
                )
            )

    return RegisterFlowReport(len(blocks), tuple(definitions), tuple(reads), tuple(calls))


def write_register_flow_report(report: RegisterFlowReport, output) -> None:
    """Escreve o relatório Markdown do rastreamento A0-A3."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M68K register-flow report",
        "",
        "> Rastreamento conservador de A0-A3 apenas em blocos alcançáveis.",
        "",
        f"- Blocos: {report.blocks}",
        f"- Definições A0-A3: {len(report.definitions)}",
        f"- Leituras de byte: {len(report.reads)}",
        f"- Chamadas JSR: {len(report.calls)}",
        "",
        "## Leituras",
        "",
        "| Offset | Registrador | Modo | Dn | Origem local | Valor |",
        "|---:|---|---|---|---:|---:|",
    ]
    for item in report.reads:
        origin = "—" if item.definition_offset is None else f"0x{item.definition_offset:06X}"
        value = "—" if item.definition_value is None else f"0x{item.definition_value:08X}"
        lines.append(
            f"| {item.offset_hex} | A{item.address_register} | {item.mode} | "
            f"D{item.data_register} | {origin} | {value} |"
        )

    lines.extend(["", "## Definições", ""])
    for item in report.definitions:
        value = "—" if item.value is None else f"0x{item.value:08X}"
        lines.append(f"- {item.offset_hex}: A{item.register} <- {item.kind} ({value})")

    lines.extend(["", "## Chamadas", ""])
    for item in report.calls:
        target = "" if item.target is None else f" -> 0x{item.target:06X}"
        lines.append(f"- {item.offset_hex}: {item.mnemonic}{target}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
