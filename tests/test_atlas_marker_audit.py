from __future__ import annotations

import json
from pathlib import Path

from dragonslayer_ptbr.text.atlas_marker_audit import audit_directory


def test_audit_counts_markers_and_preserves_source_context(tmp_path: Path) -> None:
    (tmp_path / "script_01.txt").write_bytes(
        "<COLOR 1E>日本語<COLOR OFF><WAIT CLEAR>\n".encode("cp932")
    )

    report = audit_directory(tmp_path)

    assert report["read_only"] is True
    assert report["scripts_found"] == 1
    assert report["scripts_decoded"] == 1
    assert report["lines_processed"] == 1
    assert report["decoding_errors"] == []
    assert report["marker_occurrences"] == 3
    inventory = {
        (item["kind"], item["marker"]): item
        for item in report["marker_inventory"]
    }
    assert inventory[("COLOR_MARKER", "<COLOR 1E>")]["count"] == 1
    assert inventory[("COLOR_MARKER", "<COLOR OFF>")]["count"] == 1
    assert inventory[("WAIT_MARKER", "<WAIT CLEAR>")]["count"] == 1
    assert inventory[("COLOR_MARKER", "<COLOR 1E>")]["examples"][0]["text_context"] == "日本語"


def test_audit_is_deterministic_json_and_limits_examples(tmp_path: Path) -> None:
    source = "<WAIT>日本語\n<WAIT>別の文".encode("cp932")
    (tmp_path / "script_02.txt").write_bytes(source)

    first = audit_directory(tmp_path, examples_per_marker=1)
    second = audit_directory(tmp_path, examples_per_marker=1)

    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )
    wait_marker = next(
        item for item in first["marker_inventory"] if item["marker"] == "<WAIT>"
    )
    assert wait_marker["count"] == 2
    assert len(wait_marker["examples"]) == 1
