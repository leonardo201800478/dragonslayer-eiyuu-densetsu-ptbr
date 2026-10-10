from pathlib import Path

from dragonslayer_ptbr.cli import build_parser


def test_inspect_character_table_command_arguments():
    args = build_parser().parse_args(
        ["inspect-character-table", "--rom", "roms/original/test.md"]
    )

    assert args.command == "inspect-character-table"
    assert args.rom == Path("roms/original/test.md")
    assert args.output == Path("reports/character-table-analysis.md")
