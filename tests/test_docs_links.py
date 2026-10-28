"""Repository hygiene: links in the Markdown docs resolve, and no file names an AI tool."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
LINK = re.compile(r"\]\(([^)\s]+)\)")  # the target of [text](target)
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)  # code blocks and spans: GitHub shows them as text, not links
TOOL_NAMES = re.compile(r"claude|anthropic|superpowers|chatgpt|copilot", re.IGNORECASE)
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".txt", ".csv", ".cff", ".toml", ""}


def tracked_files(pattern: str = "*") -> list[Path]:
    out = subprocess.run(["git", "ls-files", pattern], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines()]


def broken_links() -> list[str]:
    """Relative links in tracked Markdown files whose target file does not exist."""
    broken = []
    for md in tracked_files("*.md"):
        for target in LINK.findall(CODE.sub("", md.read_text(encoding="utf-8"))):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = re.sub(r"(#.*|:\d+)$", "", target)  # drop #anchor and :line
            if not (md.parent / path).exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    return broken


def files_naming_tools() -> list[str]:
    """Tracked text files that name an AI product or tool library (the project rule: no tool attribution)."""
    hits = []
    for f in tracked_files():
        if f.suffix in TEXT_SUFFIXES and f.name not in (".gitignore", Path(__file__).name) and f.exists():
            text = f.read_text(encoding="utf-8", errors="ignore")
            if TOOL_NAMES.search(text) or TOOL_NAMES.search(str(f.relative_to(ROOT))):
                hits.append(str(f.relative_to(ROOT)))
    return hits


def test_relative_links_resolve():
    assert broken_links() == []


def test_no_tool_attribution():
    assert files_naming_tools() == []
