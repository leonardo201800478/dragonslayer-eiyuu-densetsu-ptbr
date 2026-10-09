from dragonslayer_ptbr.analysis.m68k_text_parser_candidates import (
    scan_text_parser_candidates,
)


def test_text_parser_candidate_pairs_byte_read_and_control_test():
    """Reconhece MOVE.B (A3)+,D0 seguido de CMPI.B #$0E,D0."""
    rom = bytearray(0x80)
    rom[0x20:0x24] = bytes.fromhex("10 1B 0C 00")
    rom[0x24:0x26] = bytes.fromhex("00 0E")

    results = scan_text_parser_candidates(bytes(rom))

    assert len(results) == 1
    assert results[0].read_offset == 0x20
    assert results[0].test_offset == 0x22
    assert results[0].register == 0
    assert results[0].control == 0x0E


def test_text_parser_candidate_requires_same_register():
    """Evita associar leitura e comparação de registradores diferentes."""
    rom = bytearray(0x80)
    rom[0x20:0x24] = bytes.fromhex("10 1B 0C 00")
    rom[0x24:0x26] = bytes.fromhex("01")

    # Reescreve o CMPI completo: #$01,D1.
    rom[0x22:0x26] = bytes.fromhex("0C 01 00 01")

    assert scan_text_parser_candidates(bytes(rom)) == []


def test_text_parser_candidate_rejects_invalid_configuration():
    """Garante validação dos parâmetros do scanner."""
    import pytest

    with pytest.raises(ValueError, match="max_distance"):
        scan_text_parser_candidates(b"\x00" * 32, max_distance=-1)

    with pytest.raises(ValueError, match="context_size"):
        scan_text_parser_candidates(b"\x00" * 32, context_size=-1)

    with pytest.raises(ValueError, match="controls"):
        scan_text_parser_candidates(b"\x00" * 32, controls=(0x100,))


def test_text_parser_candidate_rejects_non_postincrement_read():
    """Não confunde MOVE.B (A3),D0 com MOVE.B (A3)+,D0."""
    rom = bytearray(0x80)
    rom[0x20:0x24] = bytes.fromhex("10 13 0C 00")
    rom[0x24:0x26] = bytes.fromhex("00 0E")

    assert scan_text_parser_candidates(bytes(rom)) == []
