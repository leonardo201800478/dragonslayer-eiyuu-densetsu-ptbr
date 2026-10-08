from dataclasses import dataclass
@dataclass(frozen=True)
class DragonSlayerProfile:
    """Metadados do jogo; offsets entram somente após confirmação."""
    name: str = "Dragon Slayer: Eiyuu Densetsu"
    region: str = "Japan"
    platform: str = "Mega Drive"
    text_encoding: str = "shift_jis"
    extended_control_prefix: int = 0x06
    character_table_offset: int = 0x1A551A
    character_table_end: int = 0x1A62D2
