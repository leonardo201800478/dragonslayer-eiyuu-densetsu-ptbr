from dragonslayer_ptbr.analysis.m68k_code import build_control_flow_graph
from dragonslayer_ptbr.analysis.m68k_register_flow import trace_register_flow


def test_trace_lea_a3_to_byte_read_in_reachable_block():
    rom = bytearray(0x40)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x16] = bytes.fromhex("47 F9 00 00 00 30")
    rom[0x16:0x18] = bytes.fromhex("10 1B")
    rom[0x18:0x1A] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    report = trace_register_flow(bytes(rom), blocks)

    assert len(report.reads) == 1
    assert report.reads[0].address_register == 3
    assert report.reads[0].data_register == 0
    assert report.reads[0].definition_offset == 0x10
    assert report.reads[0].definition_value == 0x30


def test_trace_does_not_invent_origin_across_block_boundary():
    rom = bytearray(0x40)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x12] = bytes.fromhex("66 06")
    rom[0x12:0x18] = bytes.fromhex("47 F9 00 00 00 30")
    rom[0x18:0x1A] = bytes.fromhex("10 1B")
    rom[0x1A:0x1C] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    report = trace_register_flow(bytes(rom), blocks)

    read = next(item for item in report.reads if item.offset == 0x18)
    assert read.definition_offset is None


def test_trace_clears_local_origin_after_jsr():
    rom = bytearray(0x50)
    rom[4:8] = (0x10).to_bytes(4, "big")
    rom[0x10:0x16] = bytes.fromhex("47 F9 00 00 00 30")
    rom[0x16:0x1C] = bytes.fromhex("4E B9 00 00 00 30")
    rom[0x1C:0x1E] = bytes.fromhex("10 1B")
    rom[0x1E:0x20] = bytes.fromhex("4E 75")
    rom[0x30:0x32] = bytes.fromhex("4E 75")

    blocks = build_control_flow_graph(bytes(rom))
    report = trace_register_flow(bytes(rom), blocks)

    read = next(item for item in report.reads if item.offset == 0x1C)
    assert read.definition_offset is None
