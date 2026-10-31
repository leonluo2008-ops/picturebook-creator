"""Portable, read-only cloud readiness check. Never prints credentials."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notion-word")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ required")
    for name in ("AGENTS.md", "SKILL.md", "SOUL.md", "scripts/notion_archive.py"):
        if not (ROOT / name).is_file():
            raise SystemExit("Missing: " + name)
    print("Repository and Python: OK")
    print("NOTION_API_KEY: " + ("configured" if os.environ.get("NOTION_API_KEY", "").strip() else "not configured"))
    if args.notion_word:
        if not os.environ.get("NOTION_API_KEY", "").strip():
            raise SystemExit("Cloud check requires NOTION_API_KEY from environment")
        sys.path.insert(0, str(ROOT / "scripts"))
        import notion_archive as n
        rows = n.query_rows(n.resolve_data_source(), args.notion_word)
        if len(rows) != 1:
            raise SystemExit("Expected exactly one ledger row, got " + str(len(rows)))
        print("Notion read-only exact lookup: OK; page_id=" + rows[0]["id"])

if __name__ == "__main__":
    main()
