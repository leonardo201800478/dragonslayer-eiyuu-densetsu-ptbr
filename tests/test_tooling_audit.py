import hashlib
import zlib
from pathlib import Path

from dragonslayer_ptbr.tooling_audit import (
    EXPECTED_CRC32,
    EXPECTED_ROM_SIZE,
    EXPECTED_SHA1,
    _inspect_dumper_source,
    build_audit_report,
    identify_rom,
    inventory_tools,
)


def test_identify_rom_returns_hashes_without_changing_bytes(tmp_path: Path):
    rom_path = tmp_path / "synthetic.bin"
    original = bytes(range(256)) * 4
    rom_path.write_bytes(original)

    result = identify_rom(rom_path)

    assert result["size"] == len(original)
    assert result["crc32"] == f"{zlib.crc32(original) & 0xFFFFFFFF:08X}"
    assert result["sha1"] == hashlib.sha1(original).hexdigest().upper()
    assert result["matches_expected"] is False
    assert rom_path.read_bytes() == original


def test_expected_rom_fingerprint_constants_are_well_formed():
    assert EXPECTED_ROM_SIZE == 2 * 1024 * 1024
    assert len(EXPECTED_CRC32) == 8
    assert len(EXPECTED_SHA1) == 40
    assert EXPECTED_CRC32 == EXPECTED_CRC32.upper()
    assert EXPECTED_SHA1 == EXPECTED_SHA1.upper()


def test_inventory_reports_expected_binaries_and_never_executes_them(tmp_path: Path):
    tools_dir = tmp_path / "ferramentas"
    binary_dir = tools_dir / "tools"
    binary_dir.mkdir(parents=True)
    (binary_dir / "Atlas.exe").write_bytes(b"synthetic executable")
    (binary_dir / "slayer1_dumper.exe").write_bytes(b"synthetic executable")

    result = inventory_tools(tools_dir)

    assert result["directory_exists"] is True
    assert result["file_count"] == 2
    assert result["expected_binaries"]["Atlas.exe"] is True
    assert result["expected_binaries"]["slayer1_dumper.exe"] is True
    assert result["expected_binaries"]["font_packer.exe"] is False
    assert result["execution_performed"] is False
    assert result["rom_modified"] is False


def test_static_dumper_inspection_detects_write_mode_and_hardcoded_layout(
    tmp_path: Path,
):
    source = tmp_path / "dumper.cpp"
    source.write_text(
        'rom = fopen( argv[2], "rb+" );\n'
        "ptr = 0x134fa0;\n"
        "for (int scene=start; scene<=224; scene++) {}\n",
        encoding="utf-8",
    )

    result = _inspect_dumper_source(source)

    assert result["available"] is True
    assert result["direct_rom_write_detected"] is True
    assert result["hardcoded_pointer_base_detected"] is True
    assert result["hardcoded_scene_range_detected"] is True
    assert len(result["warnings"]) == 3


def test_static_dumper_inspection_handles_missing_source(tmp_path: Path):
    result = _inspect_dumper_source(tmp_path / "missing.cpp")

    assert result["available"] is False
    assert result["warnings"]


def test_build_report_records_safety_and_rom_identity(tmp_path: Path):
    rom_path = tmp_path / "rom.bin"
    rom_path.write_bytes(b"not the target rom")
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    report = build_audit_report(rom_path, tools_dir)

    assert report["schema_version"] == 1
    assert report["rom"]["matches_expected"] is False
    assert report["safety"]["external_tools_executed"] is False
    assert report["safety"]["original_rom_write_attempted"] is False
