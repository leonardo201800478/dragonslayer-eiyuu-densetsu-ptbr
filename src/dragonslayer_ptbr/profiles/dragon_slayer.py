from dataclasses import dataclass
@dataclass(frozen=True)
class DragonSlayerProfile:
    """Metadados do jogo; offsets entram somente após confirmação."""
    name: str = "Dragon Slayer: Eiyuu Densetsu"
    region: str = "Japan"
    platform: str = "Mega Drive"
