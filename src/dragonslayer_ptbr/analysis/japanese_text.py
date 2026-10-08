from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JapaneseTextRegion:
    """Região candidata contendo texto japonês Shift-JIS."""

    offset: int
    end: int
    character_count: int
    control_count: int
    text: str

    @property
    def size(self) -> int:
        return self.end - self.offset

    @property
    def offset_hex(self) -> str:
        return f"0x{self.offset:06X}"

    @property
    def end_hex(self) -> str:
        return f"0x{self.end:06X}"


def _sjis_char_size(data: bytes, offset: int) -> int:
    """Retorna o tamanho de um caractere Shift-JIS válido a partir do offset."""
    value = data[offset]
    if 0x81 <= value <= 0x9F or 0xE0 <= value <= 0xFC:
        if offset + 1 >= len(data):
            return 0
        trail = data[offset + 1]
        if 0x40 <= trail <= 0x7E or 0x80 <= trail <= 0xFC:
            return 2
        return 0
    if 0x20 <= value <= 0x7E or 0xA1 <= value <= 0xDF:
        return 1
    return 0


def _japanese_ratio(text: str) -> float:
    """Calcula a proporção de caracteres japoneses no texto decodificado."""
    if not text:
        return 0.0
    japanese = sum(
        1
        for char in text
        if "\u3040" <= char <= "\u30FF"
        or "\u3400" <= char <= "\u9FFF"
    )
    return japanese / len(text)


def _consume_region(
    data: bytes,
    start: int,
    *,
    encoding: str,
    max_bytes: int,
) -> tuple[int, int, int, str] | None:
    """Consome texto e controles conhecidos a partir de um offset."""
    offset = start
    chars = 0
    controls = 0
    parts: list[str] = []

    while offset < len(data) and offset - start < max_bytes:
        value = data[offset]

        if value == 0x00:
            break

        if value == 0x01:
            parts.append(" ")
            controls += 1
            offset += 1
            continue

        if value == 0x06:
            if offset + 2 >= len(data):
                break
            parts.append(f"<CTRL {data[offset:offset + 3].hex(' ').upper()}>")
            controls += 1
            offset += 3
            continue

        size = _sjis_char_size(data, offset)
        if not size:
            break

        raw = data[offset:offset + size]
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            break

        parts.append(text)
        chars += 1
        offset += size

    if chars == 0:
        return None

    return offset, chars, controls, "".join(parts)


def scan_japanese_text(
    data: bytes,
    *,
    minimum_characters: int = 12,
    minimum_japanese_ratio: float = 0.65,
    maximum_region_size: int = 4096,
    encoding: str = "shift_jis",
    excluded_ranges: tuple[tuple[int, int], ...] = (
        (0x1A551A, 0x1A62D0),
    ),
) -> list[JapaneseTextRegion]:
    """Localiza regiões de texto japonês real sem alterar a ROM.

    O detector aceita Shift-JIS, espaços e os controles 0x01/0x06 xx yy.
    Os resultados são evidências de conteúdo textual, não identificação de
    ponteiros ou de rotinas executáveis.
    """
    if minimum_characters < 1:
        raise ValueError("minimum_characters deve ser maior que zero")
    if not 0.0 <= minimum_japanese_ratio <= 1.0:
        raise ValueError("minimum_japanese_ratio deve estar entre 0 e 1")
    if maximum_region_size < 1:
        raise ValueError("maximum_region_size deve ser maior que zero")

    regions: list[JapaneseTextRegion] = []
    offset = 0

    while offset < len(data):
        if any(start <= offset < end for start, end in excluded_ranges):
            offset += 1
            continue

        result = _consume_region(
            data,
            offset,
            encoding=encoding,
            max_bytes=maximum_region_size,
        )
        if result is None:
            offset += 1
            continue

        end, chars, controls, text = result
        plain_text = text.replace(" ", "").replace("<CTRL ", "").replace(">", "")
        if chars >= minimum_characters and _japanese_ratio(plain_text) >= minimum_japanese_ratio:
            regions.append(
                JapaneseTextRegion(
                    offset=offset,
                    end=end,
                    character_count=chars,
                    control_count=controls,
                    text=text,
                )
            )
            offset = end
        else:
            offset += 1

    return _merge_adjacent_regions(regions)


def _merge_adjacent_regions(
    regions: list[JapaneseTextRegion],
    *,
    max_gap: int = 2,
) -> list[JapaneseTextRegion]:
    """Une regiões contíguas que pertencem ao mesmo bloco textual."""
    if not regions:
        return []

    merged: list[JapaneseTextRegion] = [regions[0]]
    for current in regions[1:]:
        previous = merged[-1]
        if current.offset - previous.end <= max_gap:
            merged[-1] = JapaneseTextRegion(
                offset=previous.offset,
                end=current.end,
                character_count=previous.character_count + current.character_count,
                control_count=previous.control_count + current.control_count,
                text=previous.text + current.text,
            )
        else:
            merged.append(current)

    return merged


def write_japanese_text_report(
    regions: list[JapaneseTextRegion],
    output: str | Path,
    *,
    sample_length: int = 180,
) -> None:
    """Escreve relatório Markdown dos blocos de texto encontrados."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Japanese text regions",
        "",
        "> Evidência de texto Shift-JIS; offsets e amostras são derivados da ROM local.",
        "",
        f"Regiões encontradas: {len(regions)}",
        "",
        "| Offset | Fim | Bytes | Caracteres | Controles | Amostra |",
        "|---:|---:|---:|---:|---:|---|",
    ]

    for region in regions:
        sample = " ".join(region.text[:sample_length].split()).replace("|", "\\|")
        lines.append(
            f"| {region.offset_hex} | {region.end_hex} | {region.size} | "
            f"{region.character_count} | {region.control_count} | {sample} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
