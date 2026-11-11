"""Offline behavioral tests. No production services or credentials used."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


n = module("notion_io")
c = module("check_book")


def rt(text):
    return [{"type": "text", "text": {"content": text}}]


def fixture():
    return {"page": {"id": "page", "properties": {"状态": {"type": "select", "select": {"name": "修改中"}},
            "交付文件": {"type": "files", "files": [{"name": "prior.zip", "file": {"url": "fixture"}}]},
            "关联": {"type": "relation", "relation": [{"id": "asset-1"}]}}},
            "root_ids": ["row"], "blocks": {"row": {"id": "row", "type": "table_row", "table_row": {
                "cells": [rt("P3"), rt("The bird spreads its wings."), rt("小鸟展开翅膀，wings。") ]}}}}


def plan():
    p = fixture()["blocks"]["row"]["table_row"]
    p["cells"][2] = rt("小鸟展开翅膀，wing。")
    return {"page_id": "page", "updates": [{"block_id": "row", "payload": {"table_row": p}}]}


class NotionTests(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        with patch.object(n, "snapshot", return_value=fixture()), patch.object(n, "api") as api:
            result = n.apply(plan(), fixture())
            api.assert_not_called()
            self.assertFalse(result["execute"])

    def test_wrong_page_rejected_before_network(self):
        with patch.object(n, "snapshot") as snap:
            with self.assertRaises(ValueError):
                n.apply(dict(plan(), page_id="other"), fixture(), True)
            snap.assert_not_called()

    def test_concurrent_relation_id_change_rejected(self):
        current = fixture()
        current["page"]["properties"]["关联"]["relation"][0]["id"] = "asset-2"
        with patch.object(n, "snapshot", return_value=current), patch.object(n, "api") as api:
            with self.assertRaises(RuntimeError):
                n.apply(plan(), fixture(), True)
            api.assert_not_called()

    def test_concurrent_text_change_rejected(self):
        current = fixture()
        current["blocks"]["row"]["table_row"]["cells"][1] = rt("Someone edited this.")
        with patch.object(n, "snapshot", return_value=current), patch.object(n, "api") as api:
            with self.assertRaises(RuntimeError):
                n.apply(plan(), fixture(), True)
            api.assert_not_called()

    def test_update_preserves_english_status_and_attachment(self):
        current = fixture()
        def fake_api(path, method, body):
            self.assertEqual((path, method), ("blocks/row", "PATCH"))
            current["blocks"]["row"].update(copy.deepcopy(body))
            return {}
        with patch.object(n, "snapshot", side_effect=lambda _: copy.deepcopy(current)), patch.object(n, "api", side_effect=fake_api):
            self.assertTrue(n.apply(plan(), fixture(), True)["verified"])
        self.assertEqual(current["page"], fixture()["page"])
        self.assertEqual(current["blocks"]["row"]["table_row"]["cells"][1], fixture()["blocks"]["row"]["table_row"]["cells"][1])

    def test_server_silent_failure_is_not_success(self):
        with patch.object(n, "snapshot", return_value=fixture()), patch.object(n, "api", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "Readback mismatch"):
                n.apply(plan(), fixture(), True)

    def test_content_failure_does_not_advance_status(self):
        p = dict(plan(), properties={'状态': {'select': {'name': '待生图'}}})
        with patch.object(n, 'snapshot', return_value=fixture()), patch.object(n, 'api', return_value={}) as api:
            with self.assertRaisesRegex(RuntimeError, 'Readback mismatch'):
                n.apply(p, fixture(), True)
            self.assertEqual([call.args[0] for call in api.call_args_list], ['blocks/row'])

    def test_status_after_content_readback(self):
        current = fixture()
        events = []
        def snap(_):
            events.append('read')
            return copy.deepcopy(current)
        def fake_api(path, method, body):
            events.append(path)
            if path == 'blocks/row':
                current['blocks']['row'].update(copy.deepcopy(body))
            else:
                current['page']['properties']['状态']['select'] = body['properties']['状态']['select']
            return {}
        p = dict(plan(), properties={'状态': {'select': {'name': '待生图'}}})
        with patch.object(n, 'snapshot', side_effect=snap), patch.object(n, 'api', side_effect=fake_api):
            self.assertTrue(n.apply(p, fixture(), True)['verified'])
        self.assertEqual(events, ['read', 'blocks/row', 'read', 'pages/page', 'read'])

    def test_append_existing_book_rejected(self):
        with self.assertRaises(ValueError):
            n.apply({"page_id": "page", "append": [{"type": "paragraph"}]}, fixture(), True)

    def test_table_width_rejected(self):
        p = plan()
        p["updates"][0]["payload"]["table_row"]["cells"].pop()
        with self.assertRaises(ValueError):
            n.apply(p, fixture(), True)

    def test_all_pages_are_read(self):
        calls = []
        def fake(path, *args):
            calls.append(path)
            return {"results": [1], "has_more": True, "next_cursor": "next"} if len(calls) == 1 else {"results": [2], "has_more": False}
        with patch.object(n, "api", side_effect=fake):
            self.assertEqual(n.paged("blocks/page/children"), [1, 2])
        self.assertIn("start_cursor=next", calls[1])

    def test_merged_richtext_readback(self):
        self.assertTrue(n.verify_payload({"code": {"rich_text": rt("abcdef")}},
                                         {"code": {"rich_text": rt("abc") + rt("def")}}))

    def test_empty_page_archive_readback(self):
        before = fixture()
        before['root_ids'], before['blocks'] = [], {}
        current = copy.deepcopy(before)
        content = {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': rt('Approved manuscript')}}
        def fake_api(path, method, body):
            self.assertEqual((path, method), ('blocks/page/children', 'PATCH'))
            current['root_ids'] = ['new']
            current['blocks'] = {'new': dict(copy.deepcopy(body['children'][0]), id='new')}
            return {}
        with patch.object(n, 'snapshot', side_effect=lambda _: copy.deepcopy(current)), patch.object(n, 'api', side_effect=fake_api):
            result = n.apply({'page_id': 'page', 'append': [content]}, before, True)
            self.assertTrue(result['verified'])

    def test_missing_appended_content_detected(self):
        before = fixture()
        before['root_ids'], before['blocks'] = [], {}
        with patch.object(n, 'snapshot', return_value=before), patch.object(n, 'api', return_value={}):
            with self.assertRaisesRegex(RuntimeError, 'Append count mismatch'):
                n.apply({'page_id': 'page', 'append': [{'type': 'paragraph', 'paragraph': {'rich_text': rt('new')}}]}, before, True)


class BookTests(unittest.TestCase):
    good = '| 封面 | Wing | 翅膀，Wing |\n| P1 | The bird spreads its wings. | 小鸟展开翅膀，wing。 |'
    def check(self, text, **kwargs):
        return c.check(text, 'wing', 1, 'Wing', '翅膀，Wing', **kwargs)

    def test_grammatical_inflection_is_allowed(self):
        self.assertEqual(self.check(self.good), [])

    def test_missing_cover(self):
        self.assertTrue(self.check(self.good.split('\n')[1]))

    def test_duplicate_page(self):
        self.assertTrue(self.check(self.good + '\n' + self.good.split('\n')[1]))

    def test_split_target(self):
        self.assertTrue(self.check(self.good.replace('wing。', 'w-i-ng。')))

    def test_wrong_cover(self):
        self.assertTrue(self.check(self.good.replace('Wing |', 'Wings |')))

    def test_missing_prompt_pages(self):
        self.assertTrue(self.check(self.good, prompt='```text\n【封面】\n入画文字：Wing\n```'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
