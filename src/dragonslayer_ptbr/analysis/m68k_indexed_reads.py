from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexedByteRead:
    """Leitura MOVE.B usando endereçamento indexado por registrador."""

    offset: int
    base_register: int
    index_register: int
    index_long: bool
    destination_register: int
    context: bytes

    @property
    def offset_hex(self) -> str:
        """Retorna o offset em hexadecimal."""
        return f"0x{self.offset:06X}"

    @property
    def context_hex(self) -> str:
        """Retorna o contexto em hexadecimal."""
        return self.context.hex(" ").upper()

    @property
    def addressing(self) -> str:
        """Retorna uma descrição do modo indexado."""
        size = ".L" if self.index_long else ".W"
        return (
            f"MOVE.B (A{self.base_register},D{self.index_register}{size}),"
            f"D{self.destination_register}"
        )


def scan_indexed_byte_reads(
    data: bytes,
    *,
    context_size: int = 16,
) -> list[IndexedByteRead]:
    """Localiza MOVE.B (An,Dn.W/L),Dn na ROM.

    O scanner é deliberadamente limitado a uma forma de instrução cujo
    endereçamento indexado é inequívoco. Ele não afirma que a instrução
    pertence ao engine de texto.
    """
    if context_size < 0:
        raise ValueError("context_size deve ser maior ou igual a zero")

    results: list[IndexedByteRead] = []

    for offset in range(0, len(data) - 1, 2):
        opcode = int.from_bytes(data[offset : offset + 2], "big")

        # MOVE.B: 0001 ddd rrr 1 1 ix
        # mode=6 (110), register field = base An.
        if (opcode & 0xF138) != 0x1030:
            continue

        destination = (opcode >> 9) & 0x7
        base_register = opcode & 0x7
        index_register = (opcode >> 12) & 0x7
        index_long = bool(opcode & 0x0008)

        left = max(0, offset - context_size)
        right = min(len(data), offset + 2 + context_size)
        results.append(
            IndexedByteRead(
                offset=offset,
                base_register=base_register,
                index_register=index_register,
                index_long=index_long,
                destination_register=destination,
                context=data[left:right],
            )
        )

    return results


def write_indexed_byte_report(
    occurrences: list[IndexedByteRead],
    output,
) -> None:
    """Escreve relatório Markdown das leituras indexadas."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# M68K indexed byte reads",
        "",
        "> Evidência estática; as ocorrências não são classificadas automaticamente como texto.",
        "",
        f"Total: {len(occurrences)}",
        "",
        "| Offset | Instrução | Contexto |",
        "|---:|---|---|",
    ]

    for item in occurrences:
        lines.append(
            f"| {item.offset_hex} | {item.addressing} | {item.context_hex} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
