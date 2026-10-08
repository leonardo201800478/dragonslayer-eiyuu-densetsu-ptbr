from dragonslayer_ptbr.analysis.japanese_text import scan_japanese_text


def test_scan_japanese_text_finds_shift_jis_with_controls() -> None:
    data = (
        "これはテストです。".encode("shift_jis")
        + b"\x01"
        + "次の行です。".encode("shift_jis")
        + b"\x06\xFE\x0E"
        + "終わりです。".encode("shift_jis")
        + b"\x00"
    )

    regions = scan_japanese_text(
        data,
        minimum_characters=8,
        minimum_japanese_ratio=0.65,
    )

    assert len(regions) == 1
    assert regions[0].offset == 0
    assert regions[0].character_count >= 8
    assert regions[0].control_count == 2
    assert "これはテストです。" in regions[0].text
    assert "<CTRL 06 FE 0E>" in regions[0].text


def test_scan_japanese_text_ignores_short_runs() -> None:
    data = "短い".encode("shift_jis")
    assert scan_japanese_text(data, minimum_characters=8) == []


def test_scan_japanese_text_excludes_character_table_range() -> None:
    data = bytearray(b"\x00" * 0x100)
    start = 0x20
    text = "日本語の文字列テスト".encode("shift_jis")
    data[start : start + len(text)] = text

    regions = scan_japanese_text(
        bytes(data),
        minimum_characters=5,
        excluded_ranges=((0x10, 0x80),),
    )

    assert regions == []
