from dragonslayer_ptbr.analysis.m68k_entry_overlap import (
    find_entry_overlaps,
    render_entry_overlap_report,
)


def test_detects_entry_inside_an_instruction_from_another_root():
    rom = bytearray(0x40)
    # ADDA.L #$00000003,A5 occupies offsets 0x10 through 0x15.
    rom[0x10:0x16] = bytes.fromhex("DB FC 00 00 00 03")
    rom[0x16:0x18] = bytes.fromhex("4E 75")

    overlaps = find_entry_overlaps(bytes(rom), (0x10, 0x12))

    assert any(
        item.entry_point == 0x12
        and item.instruction_offset == 0x10
        and item.instruction_end == 0x16
        and item.instruction_bytes == bytes.fromhex("DB FC 00 00 00 03")
        for item in overlaps
    )


def test_entry_overlap_report_warns_that_runtime_is_unconfirmed():
    report = render_entry_overlap_report((0x10, 0x12), ())

    assert "não prova qual fluxo é executado em runtime" in report
    assert "Nenhuma sobreposição" in report


def test_overlap_report_includes_raw_bytes_and_half_open_range():
    rom = bytearray(0x40)
    rom[0x10:0x16] = bytes.fromhex("DB FC 00 00 00 03")
    overlaps = find_entry_overlaps(bytes(rom), (0x10, 0x12))

    report = render_entry_overlap_report((0x10, 0x12), overlaps)

    assert "`[início, fim)`" in report
    assert "`DB FC 00 00 00 03`" in report
    assert "`0x000010–0x000016`" in report


def test_rejects_unaligned_entry_points():
    try:
        find_entry_overlaps(bytes(0x20), (0x11,))
    except ValueError as exc:
        assert "desalinhada" in str(exc)
    else:
        raise AssertionError("entrada desalinhada deveria ser rejeitada")
