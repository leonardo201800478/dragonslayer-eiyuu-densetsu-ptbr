from __future__ import annotations

import json
from pathlib import Path

import pytest

from dragonslayer_ptbr.text.translation_workbench import apply_catalog, export_catalog


def test_export_catalog_finds_japanese_text_and_preserves_tags(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    script = source / "script_01.txt"
    script.write_bytes(
        "#WRITE(PtrTable)\r\nこんにちは<COLOR 1E><LINE>\r\n<END>\r\n".encode("cp932")
    )
    catalog = tmp_path / "translation.json"

    count = export_catalog(source, catalog)

    payload = json.loads(catalog.read_text(encoding="utf-8"))
    assert count == 1
    assert payload["entries"][0]["source"] == "こんにちは<COLOR 1E><LINE>"
    assert payload["entries"][0]["tags"] == ["<COLOR 1E>", "<LINE>"]
    assert script.read_bytes().startswith(b"#WRITE")


def test_apply_catalog_writes_translated_copy_without_touching_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    script = source / "script_01.txt"
    original = "#WRITE(PtrTable)\r\nこんにちは<LINE>\r\n".encode("cp932")
    script.write_bytes(original)
    catalog = tmp_path / "translation.json"
    export_catalog(source, catalog)

    payload = json.loads(catalog.read_text(encoding="utf-8"))
    payload["entries"][0]["translation"] = "Olá<LINE>"
    catalog.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "review"

    written, pending = apply_catalog(source, catalog, output)

    assert (written, pending) == (1, 0)
    assert script.read_bytes() == original
    assert (output / "script_01.txt").read_bytes().decode("utf-8") == (
        "#WRITE(PtrTable)\r\nOlá<LINE>\r\n"
    )


def test_apply_rejects_changed_inline_tags(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "script_01.txt").write_bytes("こんにちは<LINE>\n".encode("cp932"))
    catalog = tmp_path / "translation.json"
    export_catalog(source, catalog)
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    payload["entries"][0]["translation"] = "Olá"
    catalog.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="Tags/controles inline"):
        apply_catalog(source, catalog, tmp_path / "review")


def test_apply_rejects_source_changed_after_export(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    script = source / "script_01.txt"
    script.write_bytes("こんにちは<LINE>\n".encode("cp932"))
    catalog = tmp_path / "translation.json"
    export_catalog(source, catalog)
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    payload["entries"][0]["translation"] = "Olá<LINE>"
    catalog.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    script.write_bytes("さようなら<LINE>\n".encode("cp932"))

    with pytest.raises(ValueError, match="texto de origem mudou"):
        apply_catalog(source, catalog, tmp_path / "review")


def test_apply_rejects_nonempty_output_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "script_01.txt").write_bytes("こんにちは\n".encode("cp932"))
    catalog = tmp_path / "translation.json"
    export_catalog(source, catalog)
    output = tmp_path / "review"
    output.mkdir()
    (output / "keep.txt").write_text("não sobrescrever", encoding="utf-8")

    with pytest.raises(FileExistsError, match="não está vazia"):
        apply_catalog(source, catalog, output)
