from __future__ import annotations

from dataclasses import dataclass


CONTROL_VALUES = (0x01, 0x06, 0x0E, 0x00)


@dataclass(frozen=True)
class ControlTest:
    """Teste imediato 68000 potencialmente relacionado a um byte de controle."""

    offset: int
    value: int
    register: int
    context: bytes

    @property
    def offset_hex(self) -> str:
        """Retorna o offset da instrução em hexadecimal."""
        return f"0x{self.offset:06X}"

    @property
    def value_hex(self) -> str:
        """Retorna o byte comparado em hexadecimal."""
        return f"0x{self.value:02X}"

    @property
    def context_hex(self) -> str:
        """Retorna o contexto em hexadecimal."""
        return self.context.hex(" ").upper()


def scan_control_tests(
    data: bytes,
    *,
    values: tuple[int, ...] = CONTROL_VALUES,
    context_size: int = 12,
) -> list[ControlTest]:
    """Localiza CMPI.B #imm,Dn para valores de controle conhecidos.

    O padrão reconhecido é uma instrução 68000 inequívoca do formato
    CMPI.B #imm,Dn. O resultado é apenas uma evidência de comparação
    explícita; não afirma que a rotina seja o engine de texto.
    """
    if context_size < 0:
        raise ValueError("context_size deve ser maior ou igual a zero")
    for value in values:
        if not 0 <= value <= 0xFF:
            raise ValueError("values deve conter bytes entre 0 e 255")

    results: list[ControlTest] = []
    for offset in range(0, len(data) - 3, 2):
        opcode = int.from_bytes(data[offset : offset + 2], "big")
        if (opcode & 0xFFF8) != 0x0C00:
            continue

        immediate = data[offset + 3]
        if data[offset + 2] != 0 or immediate not in values:
            continue

        register = opcode & 0x7
        left = max(0, offset - context_size)
        right = min(len(data), offset + 4 + context_size)
        results.append(
            ControlTest(
                offset=offset,
                value=immediate,
                register=register,
                context=data[left:right],
            )
        )

    return results


def write_control_test_report(
    occurrences: list[ControlTest],
    output,
) -> None:
    """Escreve relatório Markdown determinístico dos testes encontrados."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# M68K control-test report",
        "",
        "> Evidência de instruções CMPI.B; não é prova de que a rotina seja o engine de texto.",
        "",
        f"Total: {len(occurrences)}",
        "",
        "| Offset | Controle | Registrador | Contexto |",
        "|---:|---:|---:|---|",
    ]
    for item in occurrences:
        lines.append(
            f"| {item.offset_hex} | {item.value_hex} | D{item.register} | "
            f"{item.context_hex} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
