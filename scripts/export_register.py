"""Write data/assumptions_register.md, a readable copy of the Excel register that GitHub can show.

Run from the repo root after editing the register:  python scripts/export_register.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # this checkout's tn2030
from tn2030.register import register_markdown

out = ROOT / "data" / "assumptions_register.md"
out.write_text(register_markdown(ROOT / "data" / "assumptions_register.xlsx"), encoding="utf-8", newline="\n")
print("wrote", out.relative_to(ROOT))
