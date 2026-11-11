"""Check actual Hermes discovery/preload with a fresh isolated profile; no model calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.profile.exists():
        raise SystemExit("Use a fresh isolated profile path")
    root = Path(__file__).resolve().parents[1]
    target = a.profile / "skills" / "creative" / "picturebook-creator"
    target.mkdir(parents=True)
    shutil.copy2(root / "SKILL.md", target / "SKILL.md")
    for folder in ("references", "scripts"):
        shutil.copytree(root / folder, target / folder, ignore=shutil.ignore_patterns("__pycache__"))
    os.environ["HERMES_HOME"] = str(a.profile.resolve())
    os.environ.pop("NOTION_API_KEY", None)
    sys.path.insert(0, str(a.runtime.resolve()))
    from agent.skill_commands import get_skill_commands, build_preloaded_skills_prompt
    from tools.skills_tool import skill_view
    commands = get_skill_commands()
    assert "/picturebook-creator" in commands
    prompt, loaded, missing = build_preloaded_skills_prompt(["picturebook-creator"])
    assert loaded and not missing and "L3b 完整文稿" in prompt
    reads = []
    for name in ["SKILL.md"] + [f"references/{p.name}" for p in (root / "references").glob("*.md")]:
        raw = skill_view("picturebook-creator", file_path=None if name == "SKILL.md" else name, preprocess=False)
        result = json.loads(raw) if isinstance(raw, str) else raw
        assert result.get("success"), name
        assert not result.get("setup_needed"), name
        reads.append(name)
    result = {"kind": "actual Hermes discovery/preload/resource reads; no model inference",
              "loaded": loaded, "missing": missing, "read_files": reads,
              "without_notion_key": True,
              "skill_sha256": hashlib.sha256((target / "SKILL.md").read_bytes()).hexdigest()}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
