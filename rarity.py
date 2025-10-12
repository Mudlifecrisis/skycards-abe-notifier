# rarity.py
import json
import math
from typing import Optional, Tuple

class RarityLookup:
    """Loads rarity or FTEA tables and returns a numeric rarity score.

    rarity = 7.5 - ln(FTEA)  (natural log)
    """
    def __init__(self, rarity_file: str = "rarity.json", ftea_file: str = "ftea.json"):
        self.by_rarity: dict[str, float] = {}
        self.by_ftea: dict[str, float] = {}
        try:
            with open(rarity_file, "r", encoding="utf-8") as f:
                self.by_rarity = {k.upper(): float(v) for k, v in json.load(f).items()}
        except Exception:
            pass
        try:
            with open(ftea_file, "r", encoding="utf-8") as f:
                self.by_ftea = {k.upper(): float(v) for k, v in json.load(f).items()}
        except Exception:
            pass

    @staticmethod
    def rarity_from_ftea(ftea: float) -> float:
        return 7.5 - math.log(max(ftea, 1e-6))

    def get(self, icao: Optional[str], iata: Optional[str]) -> Optional[float]:
        for code in [icao, iata]:
            if not code:
                continue
            code = code.upper()
            if code in self.by_rarity:
                return float(self.by_rarity[code])
            if code in self.by_ftea:
                return float(self.rarity_from_ftea(self.by_ftea[code]))
        return None

def rarity_tier(score: float) -> Tuple[str, str]:
    if score >= 7.0:
        return ("💎", "Ultra-rare")
    if score >= 5.0:
        return ("🟣", "Rare")
    if score >= 3.0:
        return ("🔵", "Uncommon")
    return ("⚪", "Common")