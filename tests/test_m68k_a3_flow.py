from dragonslayer_ptbr.analysis.m68k_a3_flow import (
    scan_a3_byte_reads,
    scan_a3_definitions,
)


def test_scan_a3_definitions_recognizes_lea_abs():
    """Reconhece LEA abs.l,A3."""
    rom = bytes.fromhex("47 F9 00 FF 20 AE")
    results = scan_a3_definitions(rom)

    assert len(results) == 1
    assert results[0].offset == 0
    assert "LEA" in results[0].instruction


def test_scan_a3_definitions_recognizes_movea_long():
    """Reconhece MOVEA.L d16(A1),A3."""
    rom = bytes.fromhex("26 69 00 12")
    results = scan_a3_definitions(rom)

    assert len(results) == 1
    assert results[0].offset == 0
    assert "MOVEA.L" in results[0].instruction


def test_scan_a3_byte_reads_recognizes_postincrement():
    """Reconhece MOVE.B (A3)+,D0."""
    rom = bytes.fromhex("10 13")
    results = scan_a3_byte_reads(rom)

    assert len(results) == 1
    assert results[0].offset == 0
    assert results[0].register == 0


def test_a3_scanners_reject_negative_context():
    """Valida contexto negativo."""
    import pytest

    with pytest.raises(ValueError, match="context_size"):
        scan_a3_definitions(b"\x00\x00", context_size=-1)

    with pytest.raises(ValueError, match="context_size"):
        scan_a3_byte_reads(b"\x00\x00", context_size=-1)
