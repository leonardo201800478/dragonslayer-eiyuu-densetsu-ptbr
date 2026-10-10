from dragonslayer_ptbr.analysis.m68k_references import find_address_references


def test_overlapping_24_and_32_bit_literals_are_kept_as_candidates():
    data = bytearray(0x100)
    data[0x10:0x13] = (0x20).to_bytes(3, "big")

    references = find_address_references(bytes(data), 0x20)

    assert {(item.offset, item.width) for item in references} == {
        (0x0F, 4),
        (0x10, 3),
    }
    assert len(references) == 2
