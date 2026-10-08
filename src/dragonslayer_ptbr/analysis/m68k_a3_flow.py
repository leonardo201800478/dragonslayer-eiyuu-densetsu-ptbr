from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class A3Definition:
    """Definição estática de A3 reconhecida por opcode 68000."""

    offset: int
    instruction: str
    context: bytes

    @property
    def offset_hex(self) -> str:
        """Retorna o offset em hexadecimal."""
        return f"0x{self.offset:06X}"

    @property
    def context_hex(self) -> str:
        """Retorna o contexto em hexadecimal."""
        return self.context.hex(" ").upper()


@dataclass(frozen=True)
class A3Use:
    """Uso de A3 como ponteiro de leitura de byte."""

    offset: int
    register: int
    context: bytes

    @property
    def offset_hex(self) -> str:
        """Retorna o offset em hexadecimal."""
        return f"0x{self.offset:06X}"

    @property
    def context_hex(self) -> str:
        """Retorna o contexto em hexadecimal."""
        return self.context.hex(" ").upper()


def scan_a3_definitions(
    data: bytes,
    *,
    context_size: int = 12,
) -> list[A3Definition]:
    """Localiza LEA/MOVEA que escrevem no registrador A3.

    A rotina reconhece somente formas cujo destino A3 é inequívoco.
    Ela não tenta desassemblar a ROM inteira.
    """
    if context_size < 0:
        raise ValueError("context_size deve ser maior ou igual a zero")

    results: list[A3Definition] = []
    for offset in range(0, len(data) - 1, 2):
        opcode = int.from_bytes(data[offset : offset + 2], "big")

        if 0x47C0 <= opcode <= 0x47FF:
            instruction = f"LEA ea,A3 (opcode 0x{opcode:04X})"
        elif 0x2640 <= opcode <= 0x267F:
            instruction = f"MOVEA.L ea,A3 (opcode 0x{opcode:04X})"
        elif 0x3640 <= opcode <= 0x367F:
            instruction = f"MOVEA.W ea,A3 (opcode 0x{opcode:04X})"
        else:
            continue

        left = max(0, offset - context_size)
        right = min(len(data), offset + 8 + context_size)
        results.append(
            A3Definition(
                offset=offset,
                instruction=instruction,
                context=data[left:right],
            )
        )

    return results


def scan_a3_byte_reads(
    data: bytes,
    *,
    context_size: int = 12,
) -> list[A3Use]:
    """Localiza MOVE.B (A3)+,Dn, usado para consumir um byte."""
    if context_size < 0:
        raise ValueError("context_size deve ser maior ou igual a zero")

    results: list[A3Use] = []
    for offset in range(0, len(data) - 1, 2):
        opcode = int.from_bytes(data[offset : offset + 2], "big")
        if (opcode & 0xF1F8) != 0x1010:
            continue

        left = max(0, offset - context_size)
        right = min(len(data), offset + 2 + context_size)
        results.append(
            A3Use(
                offset=offset,
                register=(opcode >> 9) & 0x7,
                context=data[left:right],
            )
        )

    return results


def nearest_preceding_a3_definition(
    definitions: list[A3Definition],
    use_offset: int,
) -> A3Definition | None:
    """Retorna a última definição estática de A3 antes de um uso."""
    previous = [item for item in definitions if item.offset < use_offset]
    if not previous:
        return None
    return max(previous, key=lambda item: item.offset)


def write_a3_report(
    definitions: list[A3Definition],
    uses: list[A3Use],
    output,
) -> None:
    """Escreve relatório determinístico de definições e usos de A3."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# M68K A3 data-flow evidence",
        "",
        "> Evidência estática; a proximidade entre definição e uso não prova fluxo de execução.",
        "",
        f"Definições reconhecidas de A3: {len(definitions)}",
        f"Leituras MOVE.B (A3)+: {len(uses)}",
        "",
        "## Usos de byte",
        "",
        "| Uso | Dn | Definição anterior mais próxima | Distância | Contexto |",
        "|---:|---:|---:|---:|---|",
    ]

    for use in uses:
        definition = nearest_preceding_a3_definition(definitions, use.offset)
        if definition is None:
            definition_text = "—"
            distance_text = "—"
        else:
            definition_text = definition.offset_hex
            distance_text = str(use.offset - definition.offset)

        lines.append(
            f"| {use.offset_hex} | D{use.register} | {definition_text} | "
            f"{distance_text} | {use.context_hex} |"
        )

    lines.extend(["", "## Definições", ""])
    for definition in definitions:
        lines.append(
            f"- {definition.offset_hex}: {definition.instruction} — "
            f"{definition.context_hex}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
