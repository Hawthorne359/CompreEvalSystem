"""
测评模块公共工具函数。
"""
from decimal import Decimal


def raw_max_score(indicator):
    """
    返回该指标的原始打分满分（学生/评审打分的合法上限）。

    indicator.max_score 存储的是该指标对父级聚合的实际最大贡献（已乘 grade_rules 系数），
    但学生/评审打分时填写的是"原始分"，对应的上限是规则行中的 max_score（未乘系数）。
    若指标有 grade_rules，取各规则行 max_score 的最大值作为原始满分上限；
    否则 indicator.max_score 即为原始满分，直接返回。
    """
    rules_config = indicator.grade_rules or {}
    rules = rules_config.get('rules') if isinstance(rules_config, dict) else None
    if not rules or indicator.max_score is None:
        return indicator.max_score
    candidates = [Decimal(str(r['max_score'])) for r in rules if r.get('max_score') is not None]
    return max(candidates, default=Decimal(str(indicator.max_score)))
