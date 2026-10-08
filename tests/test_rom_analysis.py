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

    target = 0x120
    pointer = target.to_bytes(2, byteorder="big")
    rom = bytearray(0x200)
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
