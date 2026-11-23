import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'public_report_checker', ROOT / 'templates/report-kit/check_report.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ReportProjectNamesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rules = self.root / 'rules.json'
        self.rules.write_text('{"room_banned": []}', encoding='utf-8')
        self.page = self.root / 'report.html'

    def check_names(self, text):
        self.page.write_text(
            '<h1>模型比较笔记</h1><p><strong>比较完成3组。</strong></p><p>'
            + text + '</p>', encoding='utf-8')
        errors, _ = checker.check(self.page, rules_path=self.rules, result_root=self.root)
        return [message for message in errors if message.startswith('内部称呼')]

    def configure(self, **settings):
        (self.root / 'project.json').write_text(json.dumps(settings), encoding='utf-8')

    def test_configured_display_name_is_checked_as_literal_text(self):
        self.configure(user_name='Mira+Research')
        self.assertTrue(self.check_names('Mira+Research 完成比较。'))
        self.assertEqual(self.check_names('MiraResearch 完成比较。'), [])

    def test_optional_project_aliases_are_checked_and_empty_entries_ignored(self):
        self.configure(user_name='', report_internal_names=['', '  ', 'Ops.bot+', 12])
        self.assertTrue(self.check_names('Ops.bot+ 完成比较。'))
        self.assertEqual(self.check_names('OpsXbot 完成比较。'), [])

    def test_missing_or_empty_settings_skip_name_checks(self):
        self.assertEqual(self.check_names('Mira+Research 完成比较。'), [])
        self.configure()
        self.assertEqual(self.check_names('Mira+Research 完成比较。'), [])

    def test_unconfigured_workflow_phrases_still_get_checked(self):
        self.assertTrue(self.check_names('可以直接发给合作者。'))
        self.assertTrue(self.check_names('交差使用 P123。'))

    def test_owner_working_page_keeps_internal_name_exemption(self):
        self.configure(user_name='Mira+Research')
        self.page.write_text(
            '<h1>阅读资料入口</h1><p><strong>3篇阅读资料。</strong></p>'
            '<p>Mira+Research</p>', encoding='utf-8')
        errors, _ = checker.check(self.page, rules_path=self.rules, result_root=self.root)
        self.assertEqual([e for e in errors if e.startswith('内部称呼')], [])

    def test_default_project_data_location_and_unicode_settings(self):
        data = self.root / 'data'
        data.mkdir()
        (data / 'project.json').write_text(
            json.dumps({'user_name': '研究同伴', 'report_internal_names': ['协作助手']}),
            encoding='utf-8-sig')
        with patch.object(checker, 'ROOT', self.root / 'templates'):
            self.assertEqual(set(checker.load_internal_names()), {'研究同伴', '协作助手'})

    def test_existing_structure_checks_keep_their_meaning(self):
        self.page.write_text('<h1>概览</h1><h2>背景</h2><p>比较3组。</p>', encoding='utf-8')
        errors, _ = checker.check(self.page, rules_path=self.rules, result_root=self.root)
        self.assertTrue(any('大标题' in e for e in errors))
        self.assertTrue(any('小标题' in e for e in errors))
        self.assertTrue(any('第一屏' in e for e in errors))

    def test_project_alias_can_record_a_decision_in_next_steps(self):
        body = '<h2>下一步</h2><p>协作助手定：先比较另一种方法。</p>'
        errors, warnings = [], []
        checker.audit_research(body, errors.append, warnings.append,
                               internal_names=['协作助手'])
        self.assertEqual([w for w in warnings if '明确推荐' in w], [])
