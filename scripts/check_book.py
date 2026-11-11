#!/usr/bin/env python3
"""Check book structure, exact cover text, whole words and narration/prompt alignment.
Does not judge English grammar, literary quality, image semantics or approvals.
"""
import argparse
import json
import re
from pathlib import Path


def rows(text):
    result = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and re.fullmatch(r"封面|P\d+", cells[0]):
            result.append(cells)
    return result


def check(narration, word, pages, cover_en, cover_cn, prompt=None):
    issues = []
    parsed = rows(narration)
    expected = ["封面"] + [f"P{i}" for i in range(1, pages + 1)]
    if [r[0] for r in parsed] != expected:
        issues.append("Narration must contain cover and every page once, in order")
    if parsed and parsed[0] != ["封面", cover_en, cover_cn]:
        issues.append("Cover row differs from selected titles")
    if any(not en or not cn for _, en, cn in parsed):
        issues.append("Empty bilingual narration cell")
    if word and "-" not in word:
        split = r"(?<![A-Za-z])" + r"[\s\-–—·/]*".join(re.escape(c) for c in word) + r"(?![A-Za-z])"
        for text in (narration, prompt or ""):
            for match in re.finditer(split, text, re.I):
                if match.group().casefold() != word.casefold():
                    issues.append("Target word split internally: " + match.group())
        for page, en, cn in parsed:
            if page != "封面" and not re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", cn):
                issues.append(f"{page}: Chinese lead-read omits exact target headword")
    if prompt is not None:
        fences = re.findall(r"^```[^\n]*$", prompt, re.M)
        if len(fences) != 2 or not prompt.strip().startswith("```") or not prompt.strip().endswith("```"):
            issues.append("Prompt must be exactly one complete fenced block")
        parts = re.split(r"^【(封面|P\d+)】\s*$", prompt, flags=re.M)
        labels = parts[1::2]
        if labels != expected:
            issues.append("Prompt must contain every page once, in order")
        by_page = {p: (en, cn) for p, en, cn in parsed}
        for page, body in zip(labels, parts[2::2]):
            label = re.search(r"^入画文字[：:]\s*(.+)$", body, re.M)
            if not label:
                issues.append(f"{page}: missing explicit visible text")
            elif page == "封面" and label.group(1).strip() != cover_en:
                issues.append("Prompt cover visible text differs from title")
            elif page != "封面" and word and not re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", label.group(1)):
                issues.append(f"{page}: visible text omits exact target label")
            line = re.search(r"^旁白[：:]\s*(.+)$", body, re.M)
            if page in by_page and (not line or not all(t in line.group(1) for t in by_page[page])):
                issues.append(f"{page}: prompt narration differs from table")
            scene = re.search(r"^生图提示词[：:]\s*(.+)$", body, re.M)
            if not scene or len(scene.group(1).strip()) < 10:
                issues.append(f"{page}: missing concrete scene description")
    return issues


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--narration", required=True)
    p.add_argument("--prompt")
    p.add_argument("--word", default="")
    p.add_argument("--pages", type=int, required=True)
    p.add_argument("--cover-en", required=True)
    p.add_argument("--cover-cn", required=True)
    a = p.parse_args()
    read = lambda name: Path(name).read_text(encoding="utf-8-sig")
    errors = check(read(a.narration), a.word, a.pages, a.cover_en, a.cover_cn, read(a.prompt) if a.prompt else None)
    print(json.dumps({"passed": not errors, "issues": errors,
                      "scope": "structure and literal alignment only; semantic review still required"}, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
