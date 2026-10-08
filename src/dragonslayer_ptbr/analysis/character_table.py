from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


CHARACTER_TABLE_OFFSET = 0x1A551A
CHARACTER_TABLE_END = 0x1A62D2

PORTUGUESE_ACCENTED = {
    "á": 0xE1, "à": 0xE0, "â": 0xE2, "ã": 0xE3,
    "é": 0xE9, "ê": 0xEA, "í": 0xED, "ó": 0xF3,
    "ô": 0xF4, "õ": 0xF5, "ú": 0xFA, "ç": 0xE7,
    "Á": 0xC1, "À": 0xC0, "Â": 0xC2, "Ã": 0xC3,
    "É": 0xC9, "Ê": 0xCA, "Í": 0xCD, "Ó": 0xD3,
    "Ô": 0xD4, "Õ": 0xD5, "Ú": 0xDA, "Ç": 0xC7,
}


@dataclass(frozen=True)
class CharacterTableEntry:
    """Entrada da tabela de códigos de caracteres observada na ROM."""

    index: int
    code: int

    @property
    def offset(self) -> int:
        return CHARACTER_TABLE_OFFSET + self.index * 2

    @property
    def offset_hex(self) -> str:
        return f"0x{self.offset:06X}"

    @property
    def code_hex(self) -> str:
        return f"0x{self.code:04X}"


def read_character_table(
    data: bytes,
    *,
    offset: int = CHARACTER_TABLE_OFFSET,
    end: int = CHARACTER_TABLE_END,
) -> list[CharacterTableEntry]:
    """Lê a tabela como palavras big-endian, sem interpretar sua semântica."""
    if offset < 0 or end <= offset:
        raise ValueError("intervalo da tabela inválido")
    if end > len(data):
        raise ValueError("fim da tabela fora da ROM")
    if (end - offset) % 2:
        raise ValueError("tamanho da tabela deve ser múltiplo de 2")

    return [
        CharacterTableEntry(
            index=index,
            code=int.from_bytes(data[position:position + 2], "big"),
        )
        for index, position in enumerate(range(offset, end, 2))
    ]


def find_code_positions(
    entries: list[CharacterTableEntry],
    code: int,
) -> list[int]:
    """Retorna os índices que contêm um determinado código."""
    if not 0 <= code <= 0xFFFF:
        raise ValueError("code deve estar entre 0 e 0xFFFF")
    return [entry.index for entry in entries if entry.code == code]


def missing_portuguese_accents(
    entries: list[CharacterTableEntry],
) -> dict[str, int]:
    """Retorna os caracteres PT-BR cujo código não existe na tabela."""
    present = {entry.code for entry in entries}
    return {
        char: code
        for char, code in PORTUGUESE_ACCENTED.items()
        if code not in present
    }


def present_portuguese_accents(
    entries: list[CharacterTableEntry],
) -> dict[str, list[int]]:
    """Retorna os caracteres acentuados já representados na tabela."""
    present = {entry.code for entry in entries}
    return {
        char: find_code_positions(entries, code)
        for char, code in PORTUGUESE_ACCENTED.items()
        if code in present
    }


def write_character_table_report(
    entries: list[CharacterTableEntry],
    output: str | Path,
) -> None:
    """Gera relatório auditável da tabela e dos caracteres PT-BR."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    missing = missing_portuguese_accents(entries)
    present = present_portuguese_accents(entries)

    lines = [
        "# Análise da tabela de caracteres",
        "",
        f"- Início: `0x{CHARACTER_TABLE_OFFSET:06X}`",
        f"- Fim observado: `0x{CHARACTER_TABLE_END:06X}`",
        f"- Entradas de 16 bits: {len(entries)}",
        "",
        "## Caracteres portugueses",
        "",
        "| Caractere | Código | Estado | Índices |",
        "|---|---:|---|---|",
    ]

    for char, code in PORTUGUESE_ACCENTED.items():
        if char in present:
            indexes = ", ".join(str(index) for index in present[char])
            state = "PRESENTE"
        else:
            indexes = "—"
            state = "AUSENTE"
        lines.append(
            f"| `{char}` | `0x{code:02X}` | {state} | {indexes} |"
        )

    lines.extend(
        [
            "",
            "## Interpretação",
            "",
            "A tabela contém códigos de caracteres japoneses e também códigos",
            "latinos de um byte. Isso demonstra que o formato de caracteres da",
            "ROM não deve ser tratado como Shift-JIS puro em todas as situações.",
            "",
            "Os códigos portugueses minúsculos acentuados listados acima não",
            "estão presentes na tabela observada. A próxima etapa é localizar",
            "a rotina que converte o código em índice/glifo antes de escolher",
            "entre substituição de entradas existentes ou extensão da tabela.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
