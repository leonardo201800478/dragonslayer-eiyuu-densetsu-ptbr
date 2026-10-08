from pathlib import Path

import pytest

from dragonslayer_ptbr.analysis.rom import analyze_rom


def test_genesis_header_is_detected(tmp_path: Path):
    """Verifica a identificação básica do header de Mega Drive."""
    rom = bytearray(0x400)
    rom[0x100:0x10F] = b"SEGA MEGA DRIVE"
    rom[0x180:0x189] = b"GM G-5542"

    path = tmp_path / "test.bin"
    path.write_bytes(rom)

    report = analyze_rom(path)

    assert report["genesis_header"]["valid"]
    assert report["genesis_header"]["serial"] == "GM G-5542"


def test_analysis_does_not_modify_rom(tmp_path: Path):
    """Garante que a análise é somente leitura."""
    path = tmp_path / "test.bin"
    original = bytes(range(256)) * 4
    path.write_bytes(original)

    analyze_rom(path)

    assert path.read_bytes() == original


def test_structural_analysis_scans_fixed_blocks(tmp_path: Path):
    """Verifica as métricas e classificações dos blocos da ROM."""
    path = tmp_path / "test.bin"
    path.write_bytes(b"\x00" * 0x100 + b"\xFF" * 0x100 + b"A" * 0x100)

    report = analyze_rom(path, block_size=0x100)
    structure = report["structure"]

    assert structure["block_size"] == 0x100
    assert structure["summary"]["block_count"] == 3
    assert structure["summary"]["classifications"]["zero_fill"] == 1
    assert structure["summary"]["classifications"]["ff_fill"] == 1
    assert structure["summary"]["classifications"]["ascii_like"] == 1
    assert structure["blocks"][0]["offset"] == 0
    assert structure["blocks"][1]["offset"] == 0x100
    assert structure["blocks"][2]["offset"] == 0x200


def test_block_size_must_be_positive(tmp_path: Path):
    """Garante erro explícito para tamanho de bloco inválido."""
    path = tmp_path / "test.bin"
    path.write_bytes(b"\x00" * 32)

    with pytest.raises(ValueError, match="block_size"):
        analyze_rom(path, block_size=0)


def test_pointer_candidates_find_repeated_big_endian_targets():
    """Verifica a descoberta de referências repetidas a um offset da ROM."""
    from dragonslayer_ptbr.analysis.pointers import scan_pointer_candidates

    target = 0x220
    pointer = target.to_bytes(2, byteorder="big")
    rom = bytearray(0x400)
    rom[0x10:0x12] = pointer
    rom[0x20:0x22] = pointer
    rom[0x30:0x32] = pointer

    result = scan_pointer_candidates(bytes(rom), minimum_references=2)
    candidates = result["16_bit"]["candidates"]

    assert candidates
    assert candidates[0]["target"] == target
    assert candidates[0]["references"] == 3


def test_pointer_scan_rejects_invalid_minimum_references():
    """Garante validação do parâmetro mínimo de referências."""
    from dragonslayer_ptbr.analysis.pointers import scan_pointer_candidates

    with pytest.raises(ValueError, match="minimum_references"):
        scan_pointer_candidates(b"\x00" * 32, minimum_references=0)


def test_pointer_scan_ignores_zero_offset_noise():
    """Garante que preenchimento 00 não seja tratado como ponteiro para zero."""
    from dragonslayer_ptbr.analysis.pointers import scan_pointer_candidates

    result = scan_pointer_candidates(b"\x00" * 0x100, minimum_references=2)

    assert result["16_bit"]["candidates"] == []
    assert result["24_bit"]["candidates"] == []
    assert result["32_bit"]["candidates"] == []


def test_pointer_tables_detect_strictly_increasing_entries():
    """Verifica uma tabela com destinos válidos, crescentes e próximos."""
    from dragonslayer_ptbr.analysis.pointers import scan_pointer_candidates

    rom = bytearray(0x500)
    targets = (0x220, 0x240, 0x280, 0x2C0)
    for index, target in enumerate(targets):
        start = index * 2
        rom[start : start + 2] = target.to_bytes(2, byteorder="big")

    result = scan_pointer_candidates(bytes(rom), minimum_table_entries=4)
    tables = result["16_bit"]["tables"]

    assert tables
    assert tables[0]["entries"] >= 4
    assert tables[0]["targets"][:4] == list(targets)
    assert tables[0]["min_delta"] == 0x20
    assert tables[0]["max_delta"] == 0x40


def test_pointer_tables_reject_repeated_targets():
    """Evita promover estruturas com destinos repetidos a tabelas."""
    from dragonslayer_ptbr.analysis.pointers import scan_pointer_candidates

    rom = bytearray(0x1000)
    targets = (0x220, 0x240, 0x240, 0x260, 0x280)
    for index, target in enumerate(targets):
        start = index * 2
        rom[start : start + 2] = target.to_bytes(2, byteorder="big")

    result = scan_pointer_candidates(bytes(rom), minimum_table_entries=4)
    tables = result["16_bit"]["tables"]

    assert tables == []


def test_pointer_tables_reject_large_target_jumps():
    """Evita sequências crescentes com saltos incompatíveis com uma tabela local."""
    from dragonslayer_ptbr.analysis.pointers import scan_pointer_candidates

    rom = bytearray(0x200000)
    targets = (0x220, 0x240, 0x5000, 0x5020)
    for index, target in enumerate(targets):
        start = index * 2
        rom[start : start + 2] = target.to_bytes(2, byteorder="big")

    result = scan_pointer_candidates(bytes(rom), minimum_table_entries=4)
    tables = result["16_bit"]["tables"]

    assert tables == []


def test_text_region_scanner_finds_delimited_candidate():
    """Verifica uma região delimitada sem assumir charset."""
    from dragonslayer_ptbr.analysis.text_regions import scan_text_regions

    rom = b"\xFF" * 16 + b"HELLO WORLD" + b"\x00" + b"\xFF" * 16

    candidates = scan_text_regions(bytes(rom), minimum_size=4)

    assert candidates
    assert candidates[0]["offset"] == 16
    assert candidates[0]["end"] == 27
    assert candidates[0]["delimiter"] == 0
    assert candidates[0]["ascii_ratio"] == 1.0


def test_text_region_scanner_rejects_invalid_parameters():
    """Garante validação dos parâmetros do scanner textual."""
    from dragonslayer_ptbr.analysis.text_regions import scan_text_regions

    with pytest.raises(ValueError, match="minimum_size"):
        scan_text_regions(b"ABC", minimum_size=0)

    with pytest.raises(ValueError, match="maximum_size"):
        scan_text_regions(b"ABC", minimum_size=8, maximum_size=4)

    with pytest.raises(ValueError, match="minimum_score"):
        scan_text_regions(b"ABC", minimum_score=1.1)

    with pytest.raises(ValueError, match="delimiters"):
        scan_text_regions(b"ABC", delimiters=())


def test_script_tokenizer_decodes_shift_jis_and_preserves_controls():
    """Verifica Shift-JIS e o controle estendido sem atribuir semântica."""
    from dragonslayer_ptbr.text.script_codec import (
        render_script,
        tokenize_script,
    )

    data = "テスト".encode("shift_jis") + b"\x01" + b"ABC" + b"\x06\xFE\x0E" + b"\x00"

    tokens = tokenize_script(data, stop_at_terminator=True)

    assert [token.kind for token in tokens] == [
        "text",
        "text",
        "text",
        "control",
        "text",
        "text",
        "text",
        "control",
        "terminator",
    ]
    assert render_script(tokens).startswith("テスト<CTRL 01>ABC<CTRL 06 FE 0E><END>")


def test_script_tokenizer_preserves_invalid_bytes():
    """Garante que bytes não reconhecidos não sejam silenciosamente descartados."""
    from dragonslayer_ptbr.text.script_codec import tokenize_script

    tokens = tokenize_script(b"A\xFFB")

    assert [token.kind for token in tokens] == ["text", "raw", "text"]
    assert tokens[1].raw == b"\xFF"


def test_script_tokenizer_rejects_invalid_control_configuration():
    """Garante validação dos parâmetros do tokenizer."""
    from dragonslayer_ptbr.text.script_codec import tokenize_script

    with pytest.raises(ValueError, match="extended_control"):
        tokenize_script(b"A", extended_control=0x100)

    with pytest.raises(ValueError, match="terminator"):
        tokenize_script(b"A", terminator=0x100)


def test_script_control_scan_preserves_absolute_offsets():
    """Verifica o mapeamento de controles com offset absoluto."""
    from dragonslayer_ptbr.analysis.script_controls import scan_script_controls

    data = "テスト".encode("shift_jis") + b"\x01ABC\x06\xFE\x0E\x00"
    occurrences = scan_script_controls(data, base_offset=0x1626B)

    assert [item.offset for item in occurrences] == [
        0x16271,
        0x16275,
        0x16278,
    ]
    assert [item.raw for item in occurrences] == [
        b"\x01",
        b"\x06\xFE\x0E",
        b"\x00",
    ]


def test_script_control_scan_rejects_negative_base_offset():
    """Garante validação do offset absoluto."""
    from dragonslayer_ptbr.analysis.script_controls import scan_script_controls

    with pytest.raises(ValueError, match="base_offset"):
        scan_script_controls(b"\x01", base_offset=-1)
