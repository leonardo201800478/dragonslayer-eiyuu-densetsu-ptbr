from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ENCODING = "shift_jis"
EXTENDED_CONTROL = 0x06
TERMINATOR = 0x00


@dataclass(frozen=True)
class ScriptToken:
    """Representa uma unidade do script sem descartar seus bytes originais."""

    kind: str
    raw: bytes
    text: str | None = None

    def render(self) -> str:
        """Converte o token para uma representação legível e reversível."""
        if self.kind == "text":
            return self.text or ""
        if self.kind == "control":
            return f"<CTRL {self.raw.hex(' ').upper()}>"
        if self.kind == "terminator":
            return "<END>"
        return f"<RAW {self.raw.hex(' ').upper()}>"


def _decode_text_byte(
    data: bytes,
    offset: int,
    encoding: str,
) -> tuple[str, int] | None:
    """Decodifica um caractere Shift-JIS a partir de um offset."""
    value = data[offset]

    if 0x81 <= value <= 0x9F or 0xE0 <= value <= 0xFC:
        if offset + 1 >= len(data):
            return None
        raw = data[offset : offset + 2]
        try:
            return raw.decode(encoding), 2
        except UnicodeDecodeError:
            return None

    if 0x20 <= value <= 0x7E or 0xA1 <= value <= 0xDF:
        raw = data[offset : offset + 1]
        try:
            return raw.decode(encoding), 1
        except UnicodeDecodeError:
            return None

    return None


def tokenize_script(
    data: bytes,
    *,
    encoding: str = DEFAULT_ENCODING,
    extended_control: int = EXTENDED_CONTROL,
    terminator: int = TERMINATOR,
    stop_at_terminator: bool = False,
) -> list[ScriptToken]:
    """Tokeniza uma região de script preservando texto e códigos de controle.

    A ROM analisada confirmou Shift-JIS em regiões textuais e um controle
    estendido iniciado por 0x06 com dois bytes adicionais. O significado
    desses controles ainda não é assumido por esta função.

    Bytes de controle simples são preservados como tokens individuais.
    Bytes que não puderem ser interpretados como texto ou controle são
    preservados como raw em vez de serem descartados.
    """
    if not 0 <= extended_control <= 0xFF:
        raise ValueError("extended_control deve estar entre 0 e 255")
    if not 0 <= terminator <= 0xFF:
        raise ValueError("terminator deve estar entre 0 e 255")

    tokens: list[ScriptToken] = []
    offset = 0

    while offset < len(data):
        value = data[offset]

        if value == terminator:
            tokens.append(ScriptToken("terminator", data[offset : offset + 1]))
            offset += 1
            if stop_at_terminator:
                break
            continue

        if value == extended_control:
            end = min(offset + 3, len(data))
            tokens.append(ScriptToken("control", data[offset:end]))
            offset = end
            continue

        if value < 0x20:
            tokens.append(ScriptToken("control", data[offset : offset + 1]))
            offset += 1
            continue

        decoded = _decode_text_byte(data, offset, encoding)
        if decoded is None:
            tokens.append(ScriptToken("raw", data[offset : offset + 1]))
            offset += 1
            continue

        text, consumed = decoded
        tokens.append(ScriptToken("text", data[offset : offset + consumed], text))
        offset += consumed

    return tokens


def render_script(tokens: list[ScriptToken]) -> str:
    """Renderiza tokens preservando controles em formato textual explícito."""
    return "".join(token.render() for token in tokens)
