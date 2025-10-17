# alerts_sources.py
import re

# Extremely simple heuristic parser; feel free to replace with a stricter one.
RE_CODE = re.compile(r"\b[A-Z0-9]{3,4}\b")

def parse_types_from_text(text: str) -> set[str]:
    return set(m.group(0).upper() for m in RE_CODE.finditer(text or ""))

class LiveSignal:
    """Keeps live sets of special types (from mirrored Discord channels)."""
    def __init__(self):
        self.glow_types: set[str] = set()
        self.rare_types: set[str] = set()
        self.mission_needles: set[str] = set()

    def handle_rare_post(self, content: str) -> None:
        self.rare_types.update(parse_types_from_text(content))

    def handle_glow_post(self, content: str) -> None:
        self.glow_types.update(parse_types_from_text(content))

    def handle_mission_post(self, content: str) -> None:
        # Save words/codes that look like targets; you can add smarter logic here.
        self.mission_needles.update(parse_types_from_text(content))