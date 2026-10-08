from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextParserCandidate:
    """Candidato a rotina que lê um byte de script e testa seu valor."""

    read_offset: int
    test_offset: int
    register: int
    control: int
    context: bytes

    @property
    def read_offset_hex(self) -> str:
        """Retorna o offset da leitura em hexadecimal."""
        return f"0x{self.read_offset:06X}"

    @property
    def test_offset_hex(self) -> str:
        """Retorna o offset do teste em hexadecimal."""
        return f"0x{self.test_offset:06X}"

    @property
    def control_hex(self) -> str:
        """Retorna o byte de controle testado."""
        return f"0x{self.control:02X}"

    @property
    def context_hex(self) -> str:
        """Retorna o contexto binário em hexadecimal."""
        return self.context.hex(" ").upper()


def scan_text_parser_candidates(
    data: bytes,
    *,
    controls: tuple[int, ...] = (0x01, 0x06, 0x0D, 0x0E),
    max_distance: int = 16,
    context_size: int = 16,
) -> list[TextParserCandidate]:
    """Encontra leitura de byte pós-incremento seguida de CMPI.B.

    O padrão principal é MOVE.B (An)+,Dn seguido, em poucos bytes, por
    CMPI.B #imm,Dn. Isso não prova que a rotina seja o engine de texto,
    mas aproxima a análise do fluxo leitura -> comparação de controle.
    """
    if max_distance < 0:
        raise ValueError("max_distance deve ser maior ou igual a zero")
    if context_size < 0:
        raise ValueError("context_size deve ser maior ou igual a zero")
    for value in controls:
        if not 0 <= value <= 0xFF:
            raise ValueError("controls deve conter bytes entre 0 e 255")

    allowed = set(controls)
    reads: list[tuple[int, int]] = []

    for offset in range(0, len(data) - 2, 2):
        opcode = int.from_bytes(data[offset : offset + 2], "big")
        # MOVE.B (An)+,Dn: source mode=3 and byte size.
        if (opcode & 0xF1F8) != 0x1010:
            continue
        reads.append((offset, (opcode >> 9) & 0x7))

    results: list[TextParserCandidate] = []
    for read_offset, register in reads:
        end = min(len(data) - 4, read_offset + max_distance)
        for test_offset in range(read_offset + 2, end + 1, 2):
            opcode = int.from_bytes(data[test_offset : test_offset + 2], "big")
            if (opcode & 0xFFF8) != 0x0C00:
                continue
            if data[test_offset + 2] != 0:
                continue
            if (opcode & 0x7) != register:
                continue
            control = data[test_offset + 3]
            if control not in allowed:
                continue

            left = max(0, read_offset - context_size)
            right = min(len(data), test_offset + 4 + context_size)
            results.append(
                TextParserCandidate(
                    read_offset=read_offset,
                    test_offset=test_offset,
                    register=register,
                    control=control,
                    context=data[left:right],
                )
            )
            break

    return results


def write_text_parser_report(
    candidates: list[TextParserCandidate],
    output,
) -> None:
    """Escreve relatório Markdown determinístico dos candidatos."""
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# M68K text-parser candidates",
        "",
        "> Evidência de leitura de byte seguida de CMPI.B; não é prova de execução.",
        "",
        f"Total: {len(candidates)}",
        "",
        "| Leitura | Teste | Registrador | Controle | Contexto |",
        "|---:|---:|---:|---:|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item.read_offset_hex} | {item.test_offset_hex} | "
            f"D{item.register} | {item.control_hex} | {item.context_hex} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
