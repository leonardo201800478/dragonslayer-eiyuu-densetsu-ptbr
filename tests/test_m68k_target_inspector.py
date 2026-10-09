from dragonslayer_ptbr.analysis.m68k_target_inspector import inspect_targets


def test_inspector_reports_direct_caller_and_target_flow():
    rom = bytearray(0x50)
    rom[4:8] = (0x10).to_bytes(4, "big")
    # Chamador: JSR $00000020; RTS
    rom[0x10:0x16] = bytes.fromhex("4E B9 00 00 00 20")
    rom[0x16:0x18] = bytes.fromhex("4E 75")
    # Alvo: MOVEQ #1,D0; RTS
    rom[0x20:0x24] = bytes.fromhex("70 01 4E 75")

    report = inspect_targets(bytes(rom), (0x20,))

    assert "Alvo 0x000020" in report
    assert "chamada em `0x000010`" in report
    assert "MOVEQ" in report
    assert "RTS" in report


def test_inspector_reports_raw_context_for_undecodable_target():
    rom = bytearray(0x40)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x12] = bytes.fromhex("4E 75")
    # 0xFFFF não é reconhecido pelo decoder atual.
    rom[0x20:0x22] = bytes.fromhex("FF FF")

    report = inspect_targets(bytes(rom), (0x20,))

    assert "não reconheceu uma instrução válida" in report
    assert "Bytes brutos ao redor do alvo" in report
    assert "`0x000018`" in report
    assert "FF FF" in report


def test_inspector_rejects_invalid_target():
    import pytest

    with pytest.raises(ValueError, match="alvo inválido"):
        inspect_targets(bytes(0x20), (0x21,))
