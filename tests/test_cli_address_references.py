from __future__ import annotations

import sys
from pathlib import Path

from dragonslayer_ptbr.cli import main


def test_scan_address_references_accepts_custom_targets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    rom_path = tmp_path / "test.bin"
    report_path = tmp_path / "references.md"
    data = bytearray(0x100)
    data[0x10:0x13] = (0x20).to_bytes(3, "big")
    rom_path.write_bytes(data)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dslayer-ptbr",
            "scan-address-references",
            "--rom",
            str(rom_path),
            "--targets",
            "0x20",
            "--output",
            str(report_path),
        ],
    )

    assert main() == 0
    report = report_path.read_text(encoding="utf-8")
    assert "## target_0x000020" in report
    # O zero anterior também forma um candidato literal de 32 bits.
    # O scanner preserva ambos os candidatos sobrepostos; nenhum prova uma referência real.
    assert "Total: 2" in report
    assert "| 0x00000F | 4 |" in report
    assert "| 0x000010 | 3 |" in report
