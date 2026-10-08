from dragonslayer_ptbr.analysis.m68k_code import (
    build_control_flow_graph,
    decode_instruction,
    reset_vector,
)


def test_decode_reset_vector_branch():
    rom = bytes.fromhex("60 02 4E 75")
    instruction = decode_instruction(rom, 0)
    assert instruction is not None
    assert instruction.mnemonic == "BRA"
    assert instruction.target == 4


def test_decode_move_byte_postincrement():
    rom = bytes.fromhex("10 18")
    instruction = decode_instruction(rom, 0)
    assert instruction is not None
    assert instruction.mnemonic == "MOVE.B (An)+,Dn"


def test_decode_cmpi_byte():
    rom = bytes.fromhex("0C 00 00 01")
    instruction = decode_instruction(rom, 0)
    assert instruction is not None
    assert instruction.mnemonic == "CMPI.B #imm,Dn"
    assert instruction.size == 4


def test_reset_vector_reads_genesis_pc():
    rom = bytearray(0x20)
    rom[4:8] = (0x10).to_bytes(4, "big")
    assert reset_vector(bytes(rom)) == 0x10


def test_cfg_follows_jsr_and_return():
    rom = bytearray(0x40)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x16] = bytes.fromhex("4E B9 00 00 00 20")
    rom[0x16:0x18] = bytes.fromhex("4E 75")
    rom[0x20:0x22] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    starts = {block.start for block in blocks}
    assert 0x10 in starts
    assert 0x20 in starts


def test_decode_bootstrap_pc_relative_lea():
    rom = bytes.fromhex("4B FA 00 7C")
    instruction = decode_instruction(rom, 0)
    assert instruction is not None
    assert instruction.mnemonic == "LEA d16(PC),An"
    assert instruction.target == 0x80
