from pathlib import Path
from dragonslayer_ptbr.analysis.rom import analyze_rom

def test_genesis_header_is_detected(tmp_path: Path):
    rom = bytearray(0x400); rom[0x100:0x10F] = b"SEGA MEGA DRIVE"; rom[0x180:0x189] = b"GM G-5542"
    path = tmp_path / "test.bin"; path.write_bytes(rom)
    report = analyze_rom(path)
    assert report["genesis_header"]["valid"]
    assert report["genesis_header"]["serial"] == "GM G-5542"

def test_analysis_does_not_modify_rom(tmp_path: Path):
    path = tmp_path / "test.bin"; original = bytes(range(256))*4; path.write_bytes(original)
    analyze_rom(path)
    assert path.read_bytes() == original
