import csv
import json
from pathlib import Path

import pytest

from dragonslayer_ptbr.translation_gui import (
    import_external_dump,
    load_catalog,
    validate_entry,
    write_qa_report,
)


def test_import_json_dump_normalizes_common_fields(tmp_path: Path) -> None:
    source = tmp_path / "external.json"
    catalog = tmp_path / "catalog.json"
    source.write_text(
        json.dumps(
            {
                "entries": [
                    {"key": "dialogue-1", "original": "こんにちは<LINE>", "translated": "Olá<LINE>"}
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert import_external_dump(source, catalog) == 1
    payload, entries = load_catalog(catalog)

    assert payload["catalog_version"] == 1
    assert entries[0]["id"] == "dialogue-1"
    assert entries[0]["source"] == "こんにちは<LINE>"
    assert entries[0]["translation"] == "Olá<LINE>"
    assert entries[0]["tags"] == ["<LINE>"]
    assert entries[0]["status"] == "TRADUZIDO"


def test_import_csv_dump_supports_source_and_translation_headers(tmp_path: Path) -> None:
    source = tmp_path / "dump.csv"
    catalog = tmp_path / "catalog.json"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "japanese", "pt_br"])
        writer.writeheader()
        writer.writerow({"id": "item-1", "japanese": "薬草", "pt_br": "Erva medicinal"})

    assert import_external_dump(source, catalog) == 1
    _payload, entries = load_catalog(catalog)
    assert entries[0]["source"] == "薬草"
    assert entries[0]["translation"] == "Erva medicinal"


def test_import_rejects_unknown_json_shape(tmp_path: Path) -> None:
    source = tmp_path / "dump.json"
    source.write_text('{"metadata": {"tool": "unknown"}}', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON não reconhecido"):
        import_external_dump(source, tmp_path / "catalog.json")


def test_validation_preserves_inline_marker_sequence() -> None:
    entry = {"source": "こんにちは<LINE><WAIT>", "translation": "Olá<LINE><WAIT>"}
    assert validate_entry(entry) == []

    entry["translation"] = "Olá<WAIT><LINE>"
    assert any("Marcadores" in problem for problem in validate_entry(entry))


def test_qa_report_is_explicitly_not_rom_ready(tmp_path: Path) -> None:
    report = write_qa_report(
        tmp_path / "qa.json",
        [
            {"id": "a", "source": "こんにちは", "translation": "Olá"},
            {"id": "b", "source": "さようなら", "translation": ""},
        ],
    )
    assert report["entries_total"] == 2
    assert report["translated"] == 1
    assert report["pending"] == 1
    assert report["rom_insertion_ready"] is False
