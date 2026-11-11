#!/usr/bin/env python3
"""Portable Notion reads and optimistic in-place updates. No credentials on disk."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request


def api(path, method="GET", body=None):
    key = os.environ.get("NOTION_API_KEY", "").strip()
    if not key:
        raise RuntimeError("NOTION_API_KEY is not available in this process")
    req = urllib.request.Request(
        "https://api.notion.com/v1/" + path.lstrip("/"),
        data=None if body is None else json.dumps(body).encode("utf-8"), method=method,
        headers={"Authorization": "Bearer " + key, "Notion-Version": "2025-09-03",
                 "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Retry reads/rate limits only. Ambiguous writes must be read back first.
            if attempt < 3 and (exc.code == 429 or (method == "GET" and exc.code >= 500)):
                time.sleep(min(2 ** attempt, 4))
                continue
            raise RuntimeError(f"Notion {method} {path}: HTTP {exc.code}; read back before retrying writes") from None


def paged(path, body=None):
    result, cursor = [], None
    while True:
        if body is None:
            query = {"page_size": 100}
            if cursor:
                query["start_cursor"] = cursor
            data = api(path + "?" + urllib.parse.urlencode(query))
        else:
            payload = dict(body, page_size=100)
            if cursor:
                payload["start_cursor"] = cursor
            data = api(path, "POST", payload)
        result.extend(data.get("results", []))
        if not data.get("has_more"):
            return result
        nxt = data.get("next_cursor")
        if not nxt or nxt == cursor:
            raise RuntimeError("Invalid pagination cursor")
        cursor = nxt


def snapshot(page_id):
    page = api(f"pages/{page_id}")
    blocks, root_ids = {}, []

    def visit(parent, root=False):
        for item in paged(f"blocks/{parent}/children"):
            block = api(f"blocks/{item['id']}")
            blocks[block["id"]] = block
            if root:
                root_ids.append(block["id"])
            if block.get("has_children"):
                visit(block["id"])
    visit(page_id, True)
    return {"page": page, "root_ids": root_ids, "blocks": blocks}


def stable(value):
    """Remove server-generated metadata; keep text, layout and user values."""
    ignored = {"object", "created_time", "last_edited_time", "created_by", "last_edited_by",
               "plain_text", "href", "request_id", "expiry_time"}
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in ignored}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def contains(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and contains(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(contains(a, b) for a, b in zip(actual, expected))
    return actual == expected


def plain(value):
    return "".join(x.get("text", {}).get("content", x.get("plain_text", "")) for x in value)


def verify_payload(actual, payload):
    # Notion may join rich_text segments. Compare full text plus other fields.
    def normalize(v):
        if isinstance(v, dict):
            return {k: (plain(x) if k in ("rich_text", "title") and isinstance(x, list)
                        else normalize(x)) for k, x in v.items()}
        if isinstance(v, list):
            return [normalize(x) for x in v]
        return v
    return contains(normalize(actual), normalize(payload))


def apply(plan, before, execute=False):
    page_id = plan["page_id"]
    if before["page"]["id"].replace("-", "") != page_id.replace("-", ""):
        raise ValueError("Snapshot is for another page")
    updates, props, append = plan.get("updates", []), plan.get("properties", {}), plan.get("append", [])
    ids = [item["block_id"] for item in updates]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate block update")
    for item in updates:
        old = before["blocks"].get(item["block_id"])
        if not old:
            raise ValueError("Update block is not in the target snapshot")
        if set(item["payload"]) != {old["type"]}:
            raise ValueError("Update must preserve block type and cannot delete/archive it")
        if old["type"] == "table_row":
            if len(item["payload"]["table_row"]["cells"]) != len(old["table_row"]["cells"]):
                raise ValueError("Table width changed")
    if append and (before["root_ids"] or updates):
        raise ValueError("Append is only supported on an empty page; update existing books in place")
    if len(append) > 100:
        raise ValueError("Append exceeds one request; prepare fewer root blocks")
    current = snapshot(page_id)
    if current["root_ids"] != before["root_ids"] or set(current["blocks"]) != set(before["blocks"]):
        raise RuntimeError("Concurrent structural edit: reread and rebuild plan")
    if stable(current["page"]["properties"]) != stable(before["page"]["properties"]):
        raise RuntimeError("Concurrent property edit: reread and rebuild plan")
    for block_id, old in before["blocks"].items():
        if stable(current["blocks"][block_id]) != stable(old):
            raise RuntimeError("Concurrent content edit: reread and rebuild plan")
    receipt = {"page_id": page_id, "execute": execute, "update_count": len(updates),
               "append_count": len(append), "property_names": list(props), "verified": False}
    if not execute:
        return receipt
    for item in updates:
        api(f"blocks/{item['block_id']}", "PATCH", item["payload"])
    if append:
        api(f"blocks/{page_id}/children", "PATCH", {"children": append})
    after = snapshot(page_id)
    for item in updates:
        if not verify_payload(after["blocks"][item["block_id"]], item["payload"]):
            raise RuntimeError("Readback mismatch in modified block")
    for name, value in before["page"]["properties"].items():
        if name not in props and value.get("type") not in ("last_edited_time", "last_edited_by"):
            if stable(after["page"]["properties"].get(name)) != stable(value):
                raise RuntimeError("Unrelated property changed during write; inspect before continuing")
    for block_id, old in before["blocks"].items():
        if block_id not in ids and stable(after["blocks"].get(block_id)) != stable(old):
            raise RuntimeError("Unrelated block changed during write; inspect before continuing")
    if append:
        if len(after["root_ids"]) != len(append):
            raise RuntimeError("Append count mismatch")
        for block_id, expected in zip(after["root_ids"], append):
            actual = after["blocks"][block_id]
            kind = expected["type"]
            content = dict(expected[kind])
            children = content.pop("children", None)
            if not verify_payload(actual, {"type": kind, kind: content}):
                raise RuntimeError("Append readback mismatch")
            if children is not None:
                got = paged(f"blocks/{block_id}/children")
                if len(got) != len(children) or not all(verify_payload(a, b) for a, b in zip(got, children)):
                    raise RuntimeError("Appended child readback mismatch")
    # Advance status/properties only after content was independently read back.
    if props:
        api(f"pages/{page_id}", "PATCH", {"properties": props})
        final = snapshot(page_id)
        if not verify_payload(final["page"]["properties"], props):
            raise RuntimeError("Readback mismatch in modified properties")
        if final["root_ids"] != after["root_ids"] or stable(final["blocks"]) != stable(after["blocks"]):
            raise RuntimeError("Content changed during property update; inspect before continuing")
        for name, value in after["page"]["properties"].items():
            if name not in props and value.get("type") not in ("last_edited_time", "last_edited_by"):
                if stable(final["page"]["properties"].get(name)) != stable(value):
                    raise RuntimeError("Unrelated property changed during final readback")
        after = final
    receipt["verified"] = True
    receipt["snapshot_sha256"] = hashlib.sha256(json.dumps(after, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    rd = sub.add_parser("read")
    rd.add_argument("--page-id", required=True)
    rd.add_argument("--out", required=True)
    q = sub.add_parser("query")
    q.add_argument("--data-source", required=True)
    q.add_argument("--book")
    q.add_argument("--word")
    q.add_argument("--status", action="append", default=[])
    ap = sub.add_parser("apply")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--receipt")
    args = parser.parse_args()
    if args.command == "read":
        Path(args.out).write_text(json.dumps(snapshot(args.page_id), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Snapshot saved: {args.out}")
    elif args.command == "query":
        schema = api(f"data_sources/{args.data_source}")["properties"]
        filters = []
        def match(name, value):
            kind = schema[name]["type"]
            if kind not in ("title", "rich_text", "select", "status"):
                raise ValueError(f"Unsupported filter property type: {name}/{kind}")
            return {"property": name, kind: {"equals": value}}
        if args.book:
            filters.append(match("排产号", args.book))
        if args.word:
            filters.append(match("核心词", args.word))
        if args.status:
            filters.append({"or": [match("状态", s) for s in args.status]})
        body = {"filter": {"and": filters}} if filters else {}
        print(json.dumps(paged(f"data_sources/{args.data_source}/query", body), ensure_ascii=False, indent=2))
    else:
        plan_path = Path(args.plan).resolve()
        plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
        before = json.loads((plan_path.parent / plan["snapshot"]).read_text(encoding="utf-8-sig"))
        result = apply(plan, before, args.execute)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.receipt:
            Path(args.receipt).write_text(output, encoding="utf-8")
        print(output)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, OSError) as exc:
        raise SystemExit(str(exc))
