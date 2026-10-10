from __future__ import annotations

import argparse
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

EXPECTED_ROM_SIZE = 2 * 1024 * 1024
EXPECTED_CRC32 = "01BC1604"
EXPECTED_SHA1 = "F67C9139BBC93F171E274A5CD3FBA66480CD8244"

EXPECTED_TOOLS = (
    "Atlas.exe",
    "slayer1_dumper.exe",
    "font_packer.exe",
    "asm68.exe",
    "xkas_gbc.exe",
)
SOURCE_PROBES = {
    "slayer1_dumper": Path("src/slayer1_dumper/dumper.cpp"),
    "font_packer": Path("src/font_packer/packer.cpp"),
}


def identify_rom(path: Path) -> dict[str, Any]:
    """Calcula identidade criptográfica da ROM sem escrever nela."""
    data = path.read_bytes()
    crc32 = f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"
    sha1 = hashlib.sha1(data).hexdigest().upper()
    return {
        "path": str(path),
        "size": len(data),
        "crc32": crc32,
        "sha1": sha1,
        "matches_expected": (
            len(data) == EXPECTED_ROM_SIZE
            and crc32 == EXPECTED_CRC32
            and sha1 == EXPECTED_SHA1
        ),
    }


def _inspect_dumper_source(path: Path) -> dict[str, Any]:
    """Inspeciona estaticamente o dumper legado; nunca executa código externo."""
    if not path.is_file():
        return {"available": False, "warnings": ["código-fonte não encontrado"]}

    source = path.read_text(encoding="utf-8", errors="replace")
    warnings: list[str] = []
    has_direct_write = 'fopen( argv[2], "rb+" )' in source or 'fopen(argv[2], "rb+")' in source
    hardcoded_pointer_base = "0x134fa0" in source.lower()
    hardcoded_scene_range = "scene<=224" in source.replace(" ", "").lower()

    if has_direct_write:
        warnings.append(
            "o código contém abertura da ROM em rb+; não executar sobre a ROM original"
        )
    if hardcoded_pointer_base:
        warnings.append("usa base de ponteiros fixa 0x134FA0")
    if hardcoded_scene_range:
        warnings.append("usa intervalo de cenas fixo até 224")

    return {
        "available": True,
        "direct_rom_write_detected": has_direct_write,
        "hardcoded_pointer_base_detected": hardcoded_pointer_base,
        "hardcoded_scene_range_detected": hardcoded_scene_range,
        "warnings": warnings,
    }


def inventory_tools(tools_dir: Path) -> dict[str, Any]:
    """Inventaria ferramentas locais e inspeciona fontes conhecidas sem executá-las."""
    root = tools_dir.resolve()
    files = sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.as_posix().casefold(),
    ) if root.is_dir() else []

    relative_files = [item.relative_to(root).as_posix() for item in files]
    expected = {
        name: any(Path(item).name.casefold() == name.casefold() for item in relative_files)
        for name in EXPECTED_TOOLS
    }
    sources = {
        name: _inspect_dumper_source(root / relative_path)
        for name, relative_path in SOURCE_PROBES.items()
    }

    return {
        "tools_dir": str(root),
        "directory_exists": root.is_dir(),
        "file_count": len(files),
        "files": relative_files,
        "expected_binaries": expected,
        "source_inspection": sources,
        "execution_performed": False,
        "rom_modified": False,
        "notes": [
            "Inventário e inspeção estática apenas; executáveis não foram iniciados.",
            "Presença de um executável não comprova compatibilidade com esta ROM ou com o sistema operacional.",
        ],
    }


def build_audit_report(rom_path: Path | None, tools_dir: Path) -> dict[str, Any]:
    """Monta um relatório JSON reproduzível para validar a instalação local."""
    report: dict[str, Any] = {
        "schema_version": 1,
        "tools": inventory_tools(tools_dir),
        "safety": {
            "external_tools_executed": False,
            "original_rom_write_attempted": False,
            "recommendation": (
                "Use uma cópia de trabalho e valide os hashes antes de qualquer teste de inserção."
            ),
        },
    }
    if rom_path is not None:
        report["rom"] = identify_rom(rom_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita a presença das ferramentas de tradução sem executá-las."
    )
    parser.add_argument("--tools-dir", type=Path, default=Path("ferramentas"))
    parser.add_argument("--rom", type=Path, help="ROM local opcional; somente leitura")
    parser.add_argument(
        "--output", type=Path, default=Path("reports/tooling-audit.json")
    )
    args = parser.parse_args()

    if args.rom is not None and not args.rom.is_file():
        parser.error(f"ROM não encontrada: {args.rom}")
    report = build_audit_report(args.rom, args.tools_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Auditoria salva em: {args.output}")
    print(f"Arquivos de ferramentas: {report['tools']['file_count']}")
    if args.rom is not None:
        status = "CONFIRMADA" if report["rom"]["matches_expected"] else "DIVERGENTE"
        print(f"Identidade da ROM: {status}")
    print("Executáveis iniciados: não")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
