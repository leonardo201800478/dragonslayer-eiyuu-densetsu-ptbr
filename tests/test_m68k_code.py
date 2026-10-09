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



def test_cfg_splits_conditional_branch_target_into_basic_blocks():
    rom = bytearray(0x30)
    rom[4:8] = (0x10).to_bytes(4, "big")
    # 0x10: BNE 0x16
    rom[0x10:0x12] = bytes.fromhex("66 04")
    rom[0x12:0x14] = bytes.fromhex("4E 71")
    rom[0x14:0x16] = bytes.fromhex("4E 71")
    rom[0x16:0x18] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    by_start = {block.start: block for block in blocks}

    assert 0x10 in by_start
    assert 0x12 in by_start
    assert 0x16 in by_start
    assert by_start[0x10].end == 0x12
    assert by_start[0x12].end == 0x16
    assert by_start[0x16].end == 0x18


def test_cfg_blocks_do_not_overlap_instruction_ranges():
    rom = bytearray(0x30)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x12] = bytes.fromhex("66 04")
    rom[0x12:0x14] = bytes.fromhex("4E 71")
    rom[0x14:0x16] = bytes.fromhex("4E 71")
    rom[0x16:0x18] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    ranges = [(block.start, block.end) for block in blocks]

    for index, (start, end) in enumerate(ranges):
        for other_start, other_end in ranges[index + 1 :]:
            assert end <= other_start or other_end <= start



def test_decode_lea_absolute_all_address_registers():
    instruction = decode_instruction(
        bytes.fromhex("4F F9 00 FF 18 3E"),
        0,
    )
    assert instruction is not None
    assert instruction.mnemonic == "LEA abs.l,A7"
    assert instruction.size == 6
    assert instruction.target == 0x00FF183E


def test_decode_lea_absolute_a1():
    instruction = decode_instruction(
        bytes.fromhex("43 F9 00 FF 00 00"),
        0,
    )
    assert instruction is not None
    assert instruction.mnemonic == "LEA abs.l,A1"
    assert instruction.target == 0x00FF0000



def test_decode_immediate_btst():
    instruction = decode_instruction(
        bytes.fromhex("08 00 00 01"),
        0,
    )
    assert instruction is not None
    assert instruction.mnemonic == "BTST #imm,<EA>"
    assert instruction.size == 4



def test_cfg_continues_after_bsr_call():
    rom = bytearray(0x40)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x14] = bytes.fromhex("61 00 00 0C")
    rom[0x14:0x16] = bytes.fromhex("4E 71")
    rom[0x20:0x22] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    by_start = {block.start: block for block in blocks}

    assert 0x10 in by_start
    assert 0x14 in by_start
    assert 0x20 in by_start
    assert by_start[0x10].end == 0x14
    assert by_start[0x14].instructions[0].offset == 0x14



def test_decode_move_byte_immediate_consumes_four_bytes():
    rom = bytes.fromhex("10 3C 00 00 4E B9 00 00 94 08")
    instruction = decode_instruction(rom, 0)

    assert instruction is not None
    assert instruction.size == 4
    assert instruction.mnemonic == "MOVE.B #imm,Dn"

    jsr = decode_instruction(rom, 4)
    assert jsr is not None
    assert jsr.size == 6
    assert jsr.mnemonic == "JSR abs.l"
    assert jsr.target == 0x00009408



def test_decode_negx_effective_address_forms():
    for opcode, suffix in (("40 00", "B"), ("40 40", "W"), ("40 80", "L")):
        instruction = decode_instruction(bytes.fromhex(opcode), 0)
        assert instruction is not None
        assert instruction.mnemonic == f"NEGX.{suffix} <EA>"
        assert instruction.size == 2


def test_decode_adda_long_immediate_consumes_long_extension():
    instruction = decode_instruction(bytes.fromhex("DB FC 00 00 00 03"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "ADDA.L #$00000003,A5"
    assert instruction.size == 6


def test_decode_suba_word_immediate_consumes_word_extension():
    instruction = decode_instruction(bytes.fromhex("96 FC 00 03"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "SUBA.W #$0003,A3"
    assert instruction.size == 4


def test_rejects_invalid_moveq_encoding():
    assert decode_instruction(bytes.fromhex("7F FF"), 0) is None


def test_decode_clr_byte_data_register():
    instruction = decode_instruction(bytes.fromhex("42 00"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "CLR.B <EA>"
    assert instruction.size == 2


def test_decode_adda_long_immediate_after_clr():
    rom = bytes.fromhex("42 00 DB FC 00 00 00 03 DD FC 00 00 00 1A")
    first = decode_instruction(rom, 0)
    second = decode_instruction(rom, 2)
    third = decode_instruction(rom, 8)
    assert first is not None and first.mnemonic == "CLR.B <EA>"
    assert second is not None and second.mnemonic == "ADDA.L #$00000003,A5"
    assert second.size == 6
    assert third is not None and third.mnemonic == "ADDA.L #$0000001A,A6"
    assert third.size == 6


def test_decode_cmpi_byte_absolute_long_consumes_all_extensions():
    instruction = decode_instruction(
        bytes.fromhex("0C 39 00 01 00 FF 1B 07 4E 75"),
        0,
    )
    assert instruction is not None
    assert instruction.mnemonic == "CMPI.B #imm,<EA>"
    assert instruction.size == 8

    following = decode_instruction(bytes.fromhex("0C 39 00 01 00 FF 1B 07 4E 75"), 8)
    assert following is not None
    assert following.mnemonic == "RTS"


def test_decode_cmpi_byte_data_register_remains_four_bytes():
    instruction = decode_instruction(bytes.fromhex("0C 00 00 01"), 0)
    assert instruction is not None
    assert instruction.mnemonic == "CMPI.B #imm,Dn"
    assert instruction.size == 4

def test_decode_ori_byte_displacement_address_consumes_extension():
    rom = bytes.fromhex("00 29 00 FF 18 4E 64 00 00 06")
    instruction = decode_instruction(rom, 0)
    assert instruction is not None
    assert instruction.mnemonic == "ORI.B #imm,<EA>"
    assert instruction.size == 6

    following = decode_instruction(rom, 6)
    assert following is not None
    assert following.mnemonic == "BCC"
    assert following.target == 16


def test_decode_addi_long_absolute_long_consumes_all_extensions():
    rom = bytes.fromhex("06 B9 00 00 00 01 00 FF 1B 07 4E 75")
    instruction = decode_instruction(rom, 0)
    assert instruction is not None
    assert instruction.mnemonic == "ADDI.L #imm,<EA>"
    assert instruction.size == 10

    following = decode_instruction(rom, 10)
    assert following is not None
    assert following.mnemonic == "RTS"
