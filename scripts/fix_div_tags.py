"""Fix accidental motion tags -> div tags in frontend."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend"
OPEN_WRONG = "<motion"
OPEN_RIGHT = "<div"
CLOSE_WRONG = "</motion>"
CLOSE_RIGHT = "</div>"

for path in ROOT.rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    fixed = text.replace(OPEN_WRONG, OPEN_RIGHT).replace(CLOSE_WRONG, CLOSE_RIGHT)
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
        print(f"fixed: {path}")
