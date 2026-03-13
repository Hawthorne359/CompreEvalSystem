"""
评分计算服务：按 ReviewRule 汇总各指标得分并计算总分。

支持任意深度指标层级（N 级树）：
  - 叶节点（无子项）：由 ScoreRecord / ArbitrationRecord 直接打分，可应用 grade_rules
  - 非叶节点：递归聚合子节点得分（sum / weighted_sum / average / sum_capped）
  - is_record_only=True 的子节点：仍写入 detail 供存档展示，但不参与父级聚合计算
  - sum_capped 节点：子项合计超过 max_score 时截断为 max_score
  - 根节点（parent=None）：聚合结果通过 category 映射到总分权重规则

总分公式：final = Σ (root_score × formula_config[root.category])

年级差异规则（grade_rules，仅叶节点有意义）：
  在读年级 = season.academic_year 起始年 - class.grade（入学年份）+ 1

性能说明：
  recompute_submission_final_score 一次性取出所有指标并在内存中建立 children_map，
  递归函数从 children_map 查找子节点，完全避免 N+1 DB 查询。
"""
from decimal import Decimal
from django.db import transaction


def _is_leaf_indicator(indicator, children_map):
    """判断指标是否叶子节点。"""
    return not children_map.get(indicator.id, [])


def submission_missing_required_leaf_indicators(submission, all_indicators=None, children_map=None):
    """
    返回该提交缺失有效得分的必需叶子指标列表。
    必需指标范围：score_source in {'self','import','reviewer'} 且为叶子节点。
    """
    from eval.models import EvalIndicator

    if all_indicators is None:
        all_indicators = list(
            EvalIndicator.objects.filter(project=submission.project).order_by('order', 'id')
        )
    if children_map is None:
        children_map = {}
        for ind in all_indicators:
            if ind.parent_id is not None:
                children_map.setdefault(ind.parent_id, []).append(ind)

    missing = []
    for ind in all_indicators:
        if ind.score_source not in ('self', 'import', 'reviewer'):
            continue
        if getattr(ind, 'is_record_only', False) and not bool(getattr(ind, 'record_only_requires_review', False)):
            continue
        if not _is_leaf_indicator(ind, children_map):
            continue
        if get_indicator_final_score(submission, ind) is None:
            missing.append({
                'indicator_id': ind.id,
                'indicator_name': ind.name,
                'score_source': ind.score_source,
            })
    return missing


def _get_year_of_study(submission):
    """
    根据 submission 的学生班级入学年份与项目测评季学年，计算学生的在读年级数（大一=1）。
    若无法解析则返回 None。
    """
    try:
        enrollment_year = int(submission.user.class_obj.grade)
    except (AttributeError, TypeError, ValueError):
        return None
    try:
        academic_year_str = submission.project.season.academic_year  # 如 "2023-2024" 或 "2023"
        season_start_year = int(str(academic_year_str).split('-')[0].strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return season_start_year - enrollment_year + 1


def _apply_grade_rule(raw_score, indicator, year_of_study):
    """
    根据指标的 grade_rules 及学生在读年级，返回应用系数后的分数（Decimal）。
    若 year_of_study 为 None 或指标未配置 grade_rules，原样返回。
    grade_rules 格式：
      {"rules": [{"min_year": 1, "max_year": 2, "max_score": 40, "coefficient": 1.0}, ...]}
    - coefficient：分数乘数（如 0.4 表示取原始分的 40%），缺省为 1.0
    - max_score：匹配该年级范围时的满分上限，超出则截断；为 null 时不限制
    """
    if year_of_study is None:
        return raw_score
    rules_config = indicator.grade_rules or {}
    rules = rules_config.get('rules') if isinstance(rules_config, dict) else None
    if not rules:
        return raw_score

    for rule in rules:
        try:
            min_y = int(rule.get('min_year', 1))
            max_y = int(rule.get('max_year', 99))
        except (TypeError, ValueError):
            continue
        if min_y <= year_of_study <= max_y:
            score = raw_score
            # 应用系数
            coeff = rule.get('coefficient')
            if coeff is not None:
                try:
                    score = score * Decimal(str(coeff))
                except Exception:
                    pass
            # 应用满分上限截断
            cap = rule.get('max_score')
            if cap is not None:
                try:
                    cap_dec = Decimal(str(cap))
                    if score > cap_dec:
                        score = cap_dec
                except Exception:
                    pass
            return score
    # 未匹配任何规则，原样返回
    return raw_score


def get_indicator_final_score(submission, indicator):
    """
    某提交在某叶子指标上的最终原始得分。
    优先级：仲裁分 > 按分配任务评分（双评/单评）> 导入评分。
    仅用于叶子指标（无子项）。返回的是 grade_rules 应用前的原始分。
    """
    from .models import ScoreRecord, ArbitrationRecord

    arb = ArbitrationRecord.objects.filter(submission=submission, indicator=indicator).first()
    if arb is not None:
        return arb.score

    # 仅采集正式分配任务通道的评分参与双评计算，避免导入或其他通道污染
    records = list(
        ScoreRecord.objects
        .filter(submission=submission, indicator=indicator, score_channel='assignment')
        .exclude(round_type=3)
        .order_by('round_type')
    )
    if not records:
        # 回退：兼容旧数据（score_channel 默认值为 'assignment'，也兼容 'import'）
        records = list(
            ScoreRecord.objects
            .filter(submission=submission, indicator=indicator)
            .exclude(round_type=3)
            .order_by('round_type')
        )
    if not records:
        return None
    rule = getattr(submission.project, 'review_rule', None)
    if not rule:
        return records[0].score
    if not rule.dual_review_enabled:
        return records[0].score
    if rule.final_score_rule == 'first':
        return records[0].score
    if rule.final_score_rule == 'max':
        return max(r.score for r in records)
    # average（默认）
    return sum(r.score for r in records) / len(records)


def _compute_node_score(submission, indicator, year_of_study, detail, children_map):
    """
    计算任意深度节点的得分，并将明细写入 detail dict。

    - 叶节点（无子项）：取 ScoreRecord 原始分，应用 grade_rules，返回处理后的分数。
    - 非叶节点：递归调用 _aggregate_children，返回聚合得分。
    - 返回 Decimal 或 None（无分时）。

    children_map: {parent_id: [child_indicator, ...]}，预先在内存中构建，避免 N+1 查询。
    """
    children = children_map.get(indicator.id, [])

    if not children:
        # 叶节点
        raw = get_indicator_final_score(submission, indicator)
        if raw is None:
            return None
        raw_dec = Decimal(str(raw))
        score_dec = _apply_grade_rule(raw_dec, indicator, year_of_study)
        detail[str(indicator.id)] = {
            'indicator_id': indicator.id,
            'name': indicator.name,
            'category': indicator.category,
            'parent_id': indicator.parent_id,
            'score_source': indicator.score_source,
            'raw_score': float(raw_dec),
            'score': float(score_dec),
            'year_of_study': year_of_study,
        }
        return score_dec
    else:
        # 非叶节点：递归聚合
        agg_score = _aggregate_children(submission, indicator, year_of_study, detail, children_map)
        if agg_score is not None:
            detail[str(indicator.id)] = {
                'indicator_id': indicator.id,
                'name': indicator.name,
                'category': indicator.category,
                'parent_id': indicator.parent_id,
                'agg_formula': indicator.agg_formula,
                'score': float(agg_score),
            }
        return agg_score


def _aggregate_children(submission, parent_indicator, year_of_study, detail, children_map):
    """
    递归聚合 parent_indicator 所有子节点的得分，返回 Decimal 或 None。
    支持 sum、weighted_sum、average、sum_capped 四种聚合方式。

    is_record_only=True 的子节点不参与计算，直接跳过（但叶节点仍会被单独计算写入 detail 供存档）。
    sum_capped 模式下，聚合后对结果做 min(sum, parent.max_score) 封顶截断。

    children_map: {parent_id: [child_indicator, ...]}，从内存查找，无 DB 查询。
    """
    children = children_map.get(parent_indicator.id, [])
    if not children:
        return None

    # is_record_only=True 的子项仍需递归计算以写入 detail 供存档，但不纳入聚合
    weighted_total = Decimal('0')
    sum_total = Decimal('0')
    scored_count = 0

    for child in children:
        s = _compute_node_score(submission, child, year_of_study, detail, children_map)
        if s is not None and not child.is_record_only:
            child_weight = Decimal(str(child.weight))
            weighted_total += s * child_weight
            sum_total += s
            scored_count += 1

    if scored_count == 0:
        return None

    agg = parent_indicator.agg_formula
    if agg == 'weighted_sum':
        result = weighted_total
    elif agg == 'average':
        result = sum_total / Decimal(str(scored_count))
    elif agg == 'sum_capped':
        # 封顶求和：子项合计不超过本节点 max_score；max_score 为 None 时不封顶
        if parent_indicator.max_score is not None:
            cap = Decimal(str(parent_indicator.max_score))
            result = min(sum_total, cap)
        else:
            result = sum_total
    else:  # sum（默认）
        result = sum_total

    return result


def recompute_submission_final_score(submission):
    """
    按权重规则重算该提交的 final_score 和 score_detail，并保存。

    层级处理逻辑（支持任意深度，无 N+1 查询）：
      1. 一次性取出项目所有指标（单条 SQL），在内存中按 parent_id 分组建立 children_map。
      2. 遍历根节点（parent_id=None），调用 _compute_node_score 递归计算得分，全程使用
         children_map，不再执行任何额外 DB 查询。
      3. 根节点有 category 则计入总分权重公式：final = Σ (root_score × formula_config[category])
    """
    from eval.models import EvalIndicator

    project = submission.project
    year_of_study = _get_year_of_study(submission)

    # 一次性取出所有指标（单条 SQL），在内存建 children_map，彻底避免 N+1
    all_indicators = list(
        EvalIndicator.objects
        .filter(project=project)
        .order_by('order', 'id')
    )

    # children_map: parent_id → 已排序的子节点列表（内存查找，无额外 DB 查询）
    # order_by('order', 'id') 已在 SQL 中处理，append 顺序即正确顺序
    children_map = {}
    for ind in all_indicators:
        if ind.parent_id is not None:
            children_map.setdefault(ind.parent_id, []).append(ind)

    root_indicators = [ind for ind in all_indicators if ind.parent_id is None]

    detail = {}
    category_scores = {}

    for ind in root_indicators:
        score = _compute_node_score(submission, ind, year_of_study, detail, children_map)
        if score is not None and ind.category:
            category_scores[ind.category] = score

    try:
        weight_rule = project.weight_rule
        config = weight_rule.formula_config or {}
    except Exception:
        config = {}

    total = Decimal('0')
    for cat, score in category_scores.items():
        weight = config.get(cat, Decimal('1'))
        if isinstance(weight, (int, float)):
            weight = Decimal(str(weight))
        total += score * weight

    missing_required = submission_missing_required_leaf_indicators(
        submission,
        all_indicators=all_indicators,
        children_map=children_map,
    )
    can_finalize_score = not missing_required

    with transaction.atomic():
        submission.score_detail = detail
        submission.final_score = total if (detail and can_finalize_score) else None
        submission.save(update_fields=['score_detail', 'final_score'])
