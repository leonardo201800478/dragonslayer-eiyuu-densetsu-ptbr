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


def test_decode_indirect_jump():
    instruction = decode_instruction(bytes.fromhex("4E D0"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "JMP (An)"


def test_decode_move_long_immediate_absolute_word():
    instruction = decode_instruction(bytes.fromhex("23 7C 53 45 47 41 2F 00"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "MOVE.L #imm,d16(An)"
    assert instruction.target is None


def test_decode_move_word_register_indirect():
    instruction = decode_instruction(bytes.fromhex("30 14"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "MOVE.W (An),Dn"


def test_decode_move_byte_d16_address_register():
    instruction = decode_instruction(bytes.fromhex("10 29 EF 01"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "MOVE.B d16(An),Dn"
    assert instruction.size == 4


def test_decode_move_word_register_to_register():
    instruction = decode_instruction(bytes.fromhex("38 85"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "MOVE.W Dn,(An)"
    assert instruction.size == 2


def test_decode_move_long_postincrement_to_address_register():
    instruction = decode_instruction(bytes.fromhex("28 9D"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "MOVE.L (An)+,(An)"
    assert instruction.size == 2


def test_decode_cmpi_byte_keeps_specific_classification():
    instruction = decode_instruction(bytes.fromhex("0C 00 00 01"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "CMPI.B #imm,Dn"


def test_cfg_ignores_unknown_indirect_target():
    rom = bytearray(0x30)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x12] = bytes.fromhex("4E 90")  # JSR (A0), destino dinâmico
    rom[0x12:0x14] = bytes.fromhex("4E 75")
    blocks = build_control_flow_graph(bytes(rom))
    assert blocks
    assert all(block.start is not None for block in blocks)


def test_decode_bootstrap_system_instructions():
    rom = bytes.fromhex(
        "4E66 4E6C 4E72 1234 4E74 0000 4E50 0004 4E58"
    )
    assert decode_instruction(rom, 0).mnemonic == "MOVE USP,An"
    assert decode_instruction(rom, 2).mnemonic == "MOVE An,USP"
    assert decode_instruction(rom, 4).mnemonic == "STOP"
    assert decode_instruction(rom, 8).mnemonic == "RTD"
    assert decode_instruction(rom, 12).mnemonic == "LINK"
    assert decode_instruction(rom, 16).mnemonic == "UNLK"
