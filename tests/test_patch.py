import json

import pytest

from dragon_slayer_ptbr.patch import PatchError, apply_manifest, apply_patches, load_manifest


def test_applies_valid_patch():
    patches = [{"offset": 1, "original": b"bc", "replacement": b"XY"}]
    assert apply_patches(b"abcd", patches) == b"aXYd"


def test_rejects_mismatched_original_bytes():
    patches = [{"offset": 1, "original": b"zz", "replacement": b"XY"}]
    with pytest.raises(PatchError, match="não correspondem"):
        apply_patches(b"abcd", patches)


def test_rejects_patch_outside_rom():
    patches = [{"offset": 3, "original": b"ab", "replacement": b"XY"}]
    with pytest.raises(PatchError, match="excede"):
        apply_patches(b"abcd", patches)


def test_rejects_overlapping_patches(tmp_path):
    manifest = tmp_path / "patch.json"
    manifest.write_text(
        json.dumps(
            {
                "patches": [
                    {"offset": 1, "original": "4142", "replacement": "5859"},
                    {"offset": 2, "original": "42", "replacement": "5A"},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PatchError, match="sobrepostas"):
        load_manifest(manifest)


def test_rejects_different_replacement_length(tmp_path):
    manifest = tmp_path / "patch.json"
    manifest.write_text(
        json.dumps({"patches": [{"offset": 0, "original": "4142", "replacement": "58"}]}),
        encoding="utf-8",
    )
    with pytest.raises(PatchError, match="mesmo tamanho"):
        load_manifest(manifest)


def test_manifest_applies_to_a_copy_and_reports_count(tmp_path):
    rom_path = tmp_path / "input.bin"
    manifest_path = tmp_path / "patch.json"
    output_path = tmp_path / "out" / "patched.bin"
    rom_path.write_bytes(b"ABCD")
    manifest_path.write_text(
        json.dumps({"patches": [{"offset": 1, "original": "4243", "replacement": "5859"}]}),
        encoding="utf-8",
    )

    assert apply_manifest(rom_path, manifest_path, output_path) == 1
    assert rom_path.read_bytes() == b"ABCD"
    assert output_path.read_bytes() == b"AXYD"


def test_empty_manifest_creates_unchanged_copy(tmp_path):
    rom_path = tmp_path / "input.bin"
    manifest_path = tmp_path / "patch.json"
    output_path = tmp_path / "output.bin"
    rom_path.write_bytes(b"ROM")
    manifest_path.write_text('{"patches": []}', encoding="utf-8")

    assert apply_manifest(rom_path, manifest_path, output_path) == 0
    assert output_path.read_bytes() == b"ROM"
