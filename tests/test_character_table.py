from dragonslayer_ptbr.analysis.character_table import (
    CHARACTER_TABLE_END,
    CHARACTER_TABLE_OFFSET,
    missing_portuguese_accents,
    present_portuguese_accents,
    read_character_table,
)


def test_read_character_table_big_endian():
    data = bytearray(0x40)
    data[0x10:0x16] = bytes.fromhex("81 40 00 C1 00 E1")

    entries = read_character_table(data, offset=0x10, end=0x16)

    assert [entry.code for entry in entries] == [0x8140, 0x00C1, 0x00E1]


def test_portuguese_accent_inventory():
    entries = read_character_table(
        bytes.fromhex("00 C0 00 C3 00 C7 00 C9 00 E1"),
        offset=0,
        end=10,
    )

    present = present_portuguese_accents(entries)
    missing = missing_portuguese_accents(entries)

    assert present["Á"] == [0]
    assert present["Ã"] == [1]
    assert present["Ç"] == [2]
    assert present["É"] == [3]
    assert "á" in missing
    assert missing["á"] == 0xE1


def test_profile_offsets_are_ordered():
    assert CHARACTER_TABLE_OFFSET < CHARACTER_TABLE_END
    assert (CHARACTER_TABLE_END - CHARACTER_TABLE_OFFSET) % 2 == 0
