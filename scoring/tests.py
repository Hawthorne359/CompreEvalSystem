"""scoring 服务层测试。"""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from scoring.services import submission_missing_required_leaf_indicators
from scoring.views import (
    _triggered_reason_by_actor_level,
    _resolve_import_actor_scope,
    _sanitize_import_policy,
)


class SubmissionCompletenessTests(TestCase):
    """校验必需叶子指标完整性判断逻辑。"""

    def _indicator(self, ind_id, score_source, parent_id=None, name='指标'):
        """构造最小可用指标对象。"""
        return SimpleNamespace(
            id=ind_id,
            name=name,
            score_source=score_source,
            parent_id=parent_id,
        )

    def test_missing_required_leaf_indicators_only(self):
        """仅返回缺失得分的必需叶子指标。"""
        submission = SimpleNamespace(project=SimpleNamespace())
        root = self._indicator(1, 'children', None, 'Root')
        leaf_self = self._indicator(2, 'self', 1, 'SelfLeaf')
        leaf_import = self._indicator(3, 'import', 1, 'ImportLeaf')
        leaf_reviewer = self._indicator(4, 'reviewer', 1, 'ReviewerLeaf')
        indicators = [root, leaf_self, leaf_import, leaf_reviewer]
        children_map = {1: [leaf_self, leaf_import, leaf_reviewer]}

        def fake_score(_, indicator):
            if indicator.id == 2:
                return 90
            if indicator.id == 4:
                return 80
            return None

        with patch('scoring.services.get_indicator_final_score', side_effect=fake_score):
            missing = submission_missing_required_leaf_indicators(
                submission,
                all_indicators=indicators,
                children_map=children_map,
            )

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['indicator_id'], 3)
        self.assertEqual(missing[0]['score_source'], 'import')

    def test_non_leaf_not_in_required_list(self):
        """非叶子节点即使无分也不应计入缺失列表。"""
        submission = SimpleNamespace(project=SimpleNamespace())
        non_leaf_import = self._indicator(10, 'import', None, 'ImportParent')
        child_leaf = self._indicator(11, 'self', 10, 'Child')
        indicators = [non_leaf_import, child_leaf]
        children_map = {10: [child_leaf]}

        with patch('scoring.services.get_indicator_final_score', return_value=None):
            missing = submission_missing_required_leaf_indicators(
                submission,
                all_indicators=indicators,
                children_map=children_map,
            )

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['indicator_id'], 11)


class ObjectionIntegrationHelperTests(TestCase):
    """异议仲裁落分辅助逻辑测试。"""

    def test_triggered_reason_mapping(self):
        """不同处理层级应映射到对应仲裁来源。"""
        self.assertEqual(_triggered_reason_by_actor_level(1), 'assistant_objection')
        self.assertEqual(_triggered_reason_by_actor_level(2), 'counselor_objection')
        self.assertEqual(_triggered_reason_by_actor_level(3), 'director_objection')
        self.assertEqual(_triggered_reason_by_actor_level(5), 'admin_objection')


class ImportScopeHelperTests(TestCase):
    """导入权限作用域辅助函数测试。"""

    def test_resolve_scope_prefers_max_role_level(self):
        user = SimpleNamespace(current_role=SimpleNamespace(level=2))
        with patch('scoring.views._user_max_role_level', return_value=5), patch(
            'scoring.views._get_counselor_class_ids', return_value={1, 2}
        ):
            scope = _resolve_import_actor_scope(user)
        self.assertEqual(scope['effective_level'], 5)
        self.assertEqual(scope['current_level'], 2)
        self.assertEqual(scope['max_level'], 5)

    def test_resolve_scope_director_requires_department(self):
        user = SimpleNamespace(current_role=SimpleNamespace(level=2), department_id=10)
        with patch('scoring.views._user_max_role_level', return_value=3), patch(
            'scoring.views._resolve_director_department_id', return_value=10
        ):
            scope = _resolve_import_actor_scope(user)
        self.assertEqual(scope['effective_level'], 3)
        self.assertEqual(scope['department_id'], 10)

    def test_import_policy_default_and_invalid(self):
        self.assertEqual(
            _sanitize_import_policy({}),
            {'import_mode': 'subordinate_self', 'subordinate_requires_approval': True},
        )
        self.assertEqual(
            _sanitize_import_policy({'import_mode': 'bad', 'subordinate_requires_approval': 0}),
            {'import_mode': 'subordinate_self', 'subordinate_requires_approval': False},
        )
