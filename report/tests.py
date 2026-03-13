"""报表导出服务回归测试。"""
from django.test import TestCase

from eval.models import EvalIndicator, EvalProject, EvalSeason
from report.services import get_project_export_catalog


class ReportExportCatalogRegressionTests(TestCase):
    """覆盖仅记录模块字段口径与排序稳定性回归。"""

    def setUp(self):
        self.season = EvalSeason.objects.create(
            name='2025-2026 学年',
            academic_year='2025-2026',
            semester='1',
            status='ongoing',
        )
        self.project = EvalProject.objects.create(
            season=self.season,
            name='综合测评',
            status='ongoing',
        )

    def test_record_only_field_common_policy(self):
        """仅记录模块未推评审时：保留记录值，隐藏确认分，过程记录按开关决定。"""
        leaf = EvalIndicator.objects.create(
            project=self.project,
            name='B1 必修课门次',
            score_source='self',
            is_record_only=True,
            require_process_record=False,
            record_only_requires_review=False,
            order=1,
        )
        catalog = get_project_export_catalog(self.project, view_mode='all')
        fields = [item for item in catalog['all_fields'] if item.get('indicator_id') == leaf.id]
        key_map = {item['split_type']: item for item in fields}

        self.assertTrue(key_map['self_score']['is_common'])
        self.assertNotIn('final_adopted_score', key_map)
        self.assertFalse(key_map['process_record']['is_common'])

    def test_indicator_order_is_stable_by_module_then_indicator(self):
        """字段顺序保持 module -> indicator -> field_type 的稳定排序。"""
        EvalIndicator.objects.create(
            project=self.project,
            name='A2 项目',
            score_source='self',
            require_process_record=True,
            order=20,
        )
        EvalIndicator.objects.create(
            project=self.project,
            name='B1 项目',
            score_source='self',
            is_record_only=True,
            require_process_record=False,
            record_only_requires_review=False,
            order=30,
        )
        EvalIndicator.objects.create(
            project=self.project,
            name='A1 项目',
            score_source='self',
            require_process_record=True,
            order=10,
        )

        catalog = get_project_export_catalog(self.project, view_mode='all')
        indicator_fields = [item for item in catalog['all_fields'] if item.get('category_id') == 'indicators']
        pairs = [(item.get('module_key'), item.get('indicator_key')) for item in indicator_fields]
        first_a1 = pairs.index(('A', 'A1'))
        first_a2 = pairs.index(('A', 'A2'))
        first_b1 = pairs.index(('B', 'B1'))

        self.assertLess(first_a1, first_a2)
        self.assertLess(first_a2, first_b1)
