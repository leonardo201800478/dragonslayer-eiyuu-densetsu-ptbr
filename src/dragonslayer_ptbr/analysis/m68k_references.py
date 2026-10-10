from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class M68KReference:
    """Referência literal a um endereço da ROM encontrada no código/dados."""

    offset: int
    target: int
    width: int
    context: bytes
    instruction: str | None = None

    @property
    def offset_hex(self) -> str:
        """Retorna o offset da referência em hexadecimal."""
        return f"0x{self.offset:06X}"

    @property
    def target_hex(self) -> str:
        """Retorna o destino referenciado em hexadecimal."""
        return f"0x{self.target:06X}"

    @property
    def context_hex(self) -> str:
        """Retorna o contexto binário em hexadecimal."""
        return self.context.hex(" ").upper()


_ABSOLUTE_LONG = {
    0x41F9: "LEA abs.l",
    0x4879: "PEA abs.l",
    0x4EB9: "JSR abs.l",
    0x4EF9: "JMP abs.l",
}

_MOVEA_LONG_IMMEDIATE_BASE = 0x207C


def _instruction_name(opcode: int) -> str | None:
    """Identifica apenas instruções cujo formato de endereço é inequívoco."""
    if opcode in _ABSOLUTE_LONG:
        return _ABSOLUTE_LONG[opcode]
    if (opcode & 0xF1FF) == _MOVEA_LONG_IMMEDIATE_BASE:
        register = (opcode >> 9) & 0x7
        return f"MOVEA.L #imm,A{register}"
    return None


def find_address_references(
    data: bytes,
    target: int,
    *,
    rom_size: int | None = None,
    include_three_byte: bool = True,
    include_four_byte: bool = True,
    context_size: int = 8,
) -> list[M68KReference]:
    """Localiza representações big-endian de um endereço da ROM.

    A função não tenta desassemblar a ROM. Ela procura o endereço como
    literal de 24 e/ou 32 bits e, quando os quatro bytes anteriores formam
    um opcode 68000 conhecido, registra uma classificação instrucional.

    Ocorrências de larguras diferentes são preservadas mesmo quando seus
    intervalos se sobrepõem. Por exemplo, os bytes 00 00 20 podem formar um
    candidato de 24 bits em um offset e, junto a um zero anterior, um candidato
    de 32 bits no offset anterior. Isso é uma ambiguidade literal, não prova
    de duas referências reais nem motivo para descartar um dos candidatos.
    """
    if target < 0:
        raise ValueError("target deve ser maior ou igual a zero")
    if target > 0xFFFFFFFF:
        raise ValueError("target deve caber em 32 bits")
    if not include_three_byte and not include_four_byte:
        raise ValueError("pelo menos uma largura deve ser habilitada")
    if context_size < 0:
        raise ValueError("context_size deve ser maior ou igual a zero")

    logical_size = len(data) if rom_size is None else rom_size
    if logical_size <= 0:
        raise ValueError("rom_size deve ser maior que zero")
    if target >= logical_size:
        raise ValueError("target deve estar dentro da ROM")

    widths = []
    if include_three_byte and target <= 0xFFFFFF:
        widths.append((3, target.to_bytes(3, "big")))
    if include_four_byte:
        widths.append((4, target.to_bytes(4, "big")))

    results: list[M68KReference] = []
    seen: set[tuple[int, int]] = set()

    for width, needle in widths:
        start = 0
        while True:
            offset = data.find(needle, start)
            if offset < 0:
                break
            start = offset + 1

            key = (offset, width)
            if key in seen:
                continue
            seen.add(key)

            instruction = None
            if offset >= 2:
                opcode = int.from_bytes(data[offset - 2 : offset], "big")
                instruction = _instruction_name(opcode)

            left = max(0, offset - context_size)
            right = min(len(data), offset + width + context_size)
            results.append(
                M68KReference(
                    offset=offset,
                    target=target,
                    width=width,
                    context=data[left:right],
                    instruction=instruction,
                )
            )

    return sorted(results, key=lambda item: (item.offset, item.width))


def scan_known_targets(
    data: bytes,
    targets: dict[str, int],
    *,
    context_size: int = 8,
) -> dict[str, list[M68KReference]]:
    """Procura vários alvos confirmados e retorna resultados por nome."""
    return {
        name: find_address_references(
            data,
            target,
            context_size=context_size,
        )
        for name, target in targets.items()
    }


def write_reference_report(
    references: dict[str, list[M68KReference]],
    output,
) -> None:
    """Escreve relatório Markdown determinístico das referências encontradas."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# M68K reference report",
        "",
        "> Evidência literal; não é um desassemblador nem prova de execução.",
        "",
    ]

    for name, items in references.items():
        lines.extend(
            [
                f"## {name}",
                "",
                f"Total: {len(items)}",
                "",
                "| Offset | Largura | Instrução reconhecida | Contexto |",
                "|---:|---:|---|---|",
            ]
        )
        for item in items:
            instruction = item.instruction or "—"
            lines.append(
                f"| {item.offset_hex} | {item.width} | {instruction} | "
                f"{item.context_hex} |"
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
