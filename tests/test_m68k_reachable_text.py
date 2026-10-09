from dragonslayer_ptbr.analysis.m68k_code import CodeBlock, M68KInstruction
from dragonslayer_ptbr.analysis.m68k_reachable_text import scan_reachable_text_candidates


def test_reachable_scanner_pairs_postincrement_read_and_control_test():
    data = bytearray(0x40)
    data[0x10:0x14] = bytes.fromhex("10 1B 0C 00")
    data[0x14:0x16] = bytes.fromhex("00 0E")
    block = CodeBlock(
        start=0x10,
        end=0x16,
        instructions=(
            M68KInstruction(0x10, 2, "MOVE.B (An)+,Dn"),
            M68KInstruction(0x12, 4, "CMPI.B #imm,Dn"),
        ),
        stopped_reason="unknown_opcode",
    )

    results = scan_reachable_text_candidates(bytes(data), [block])

    assert len(results) == 1
    assert results[0].block_start == 0x10
    assert results[0].read_offset == 0x10
    assert results[0].test_offset == 0x12
    assert results[0].address_register == 3
    assert results[0].data_register == 0
    assert results[0].control == 0x0E


def test_reachable_scanner_rejects_different_data_register():
    data = bytearray(0x40)
    data[0x10:0x12] = bytes.fromhex("10 1B")
    data[0x12:0x16] = bytes.fromhex("0C 01 00 01")
    block = CodeBlock(
        start=0x10,
        end=0x16,
        instructions=(
            M68KInstruction(0x10, 2, "MOVE.B (An)+,Dn"),
            M68KInstruction(0x12, 4, "CMPI.B #imm,Dn"),
        ),
        stopped_reason="unknown_opcode",
    )

    assert scan_reachable_text_candidates(bytes(data), [block]) == []


def test_reachable_scanner_ignores_pattern_outside_reachable_blocks():
    data = bytearray(0x40)
    data[0x10:0x16] = bytes.fromhex("10 1B 0C 00 00 0E")

    assert scan_reachable_text_candidates(bytes(data), []) == []


def test_reachable_scanner_rejects_invalid_parameters():
    import pytest

    with pytest.raises(ValueError, match="max_distance"):
        scan_reachable_text_candidates(b"\x00" * 32, [], max_distance=-1)
    with pytest.raises(ValueError, match="controls"):
        scan_reachable_text_candidates(b"\x00" * 32, [], controls=(0x100,))
