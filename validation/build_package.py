"""Build an installable skill, excluding tests, evidence and repository metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(out):
    files = [ROOT / "SKILL.md"]
    files += sorted((ROOT / "references").glob("*.md"))
    files += sorted((ROOT / "scripts").glob("*.py"))
    manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, "picturebook-creator/" + p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(out) as z:
        assert len(z.namelist()) == len(files)
        assert z.testzip() is None
        for name, digest in manifest.items():
            assert hashlib.sha256(z.read("picturebook-creator/" + name)).hexdigest() == digest
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(out), "file_count": len(files), "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    print(json.dumps(build(p.parse_args().out), ensure_ascii=False, indent=2))
