"""
数据变化信号处理器：监听关键模型的 post_save / post_delete，
通过 SSE 推送通知相关用户刷新数据。

信号处理只做一件事：调用 publish() 推送事件，不修改任何业务逻辑。
"""
import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from realtime.registry import publish, broadcast

logger = logging.getLogger(__name__)


def _safe_publish(user_id, event_dict):
    """安全地推送事件，捕获异常防止影响主流程。"""
    try:
        publish(user_id, event_dict)
    except Exception as exc:
        logger.warning('SSE publish failed: %s', exc)


def _safe_broadcast(event_dict):
    """安全地广播事件，捕获异常防止影响主流程。"""
    try:
        broadcast(event_dict)
    except Exception as exc:
        logger.warning('SSE broadcast failed: %s', exc)


# ── StudentSubmission ──────────────────────────────────────────────

@receiver(post_save, sender='submission.StudentSubmission')
def on_submission_save(sender, instance, **kwargs):
    """提交状态变化时通知提交者 + 广播给所有在线用户（审核老师等）。"""
    _safe_publish(instance.user_id, {
        'type': 'data_changed',
        'model': 'submission',
        'id': instance.id,
    })
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'submission',
        'id': instance.id,
    })


@receiver(post_delete, sender='submission.StudentSubmission')
def on_submission_delete(sender, instance, **kwargs):
    """提交删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'submission',
    })


# ── Appeal ─────────────────────────────────────────────────────────

@receiver(post_save, sender='appeal.Appeal')
def on_appeal_save(sender, instance, **kwargs):
    """申诉状态变化时通知申诉者和处理人。"""
    if hasattr(instance, 'submission') and instance.submission:
        _safe_publish(instance.submission.user_id, {
            'type': 'data_changed',
            'model': 'appeal',
            'id': instance.id,
        })
    if instance.handler_id:
        _safe_publish(instance.handler_id, {
            'type': 'data_changed',
            'model': 'appeal',
            'id': instance.id,
        })
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'appeal',
        'id': instance.id,
    })


@receiver(post_delete, sender='appeal.Appeal')
def on_appeal_delete(sender, instance, **kwargs):
    """申诉删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'appeal',
    })


# ── ScoreRecord ────────────────────────────────────────────────────

@receiver(post_save, sender='scoring.ScoreRecord')
def on_score_save(sender, instance, **kwargs):
    """评分记录变化时通知被评分学生。"""
    if hasattr(instance, 'submission') and instance.submission:
        _safe_publish(instance.submission.user_id, {
            'type': 'data_changed',
            'model': 'score',
            'id': instance.id,
        })
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'score',
        'id': instance.id,
    })


@receiver(post_delete, sender='scoring.ScoreRecord')
def on_score_delete(sender, instance, **kwargs):
    """评分删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'score',
    })


# ── LateSubmitRequest ──────────────────────────────────────────────

@receiver(post_save, sender='audit.LateSubmitRequest')
def on_late_request_save(sender, instance, **kwargs):
    """补交申请变化时通知申请者 + 广播给管理员。"""
    if hasattr(instance, 'submission') and instance.submission:
        _safe_publish(instance.submission.user_id, {
            'type': 'data_changed',
            'model': 'late_request',
            'id': instance.id,
        })
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'late_request',
        'id': instance.id,
    })


@receiver(post_delete, sender='audit.LateSubmitRequest')
def on_late_request_delete(sender, instance, **kwargs):
    """补交申请删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'late_request',
    })


# ── EvalSeason ─────────────────────────────────────────────────────

@receiver(post_save, sender='eval.EvalSeason')
def on_season_save(sender, instance, **kwargs):
    """测评周期变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'season',
        'id': instance.id,
    })


@receiver(post_delete, sender='eval.EvalSeason')
def on_season_delete(sender, instance, **kwargs):
    """测评周期删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'season',
    })


# ── EvalProject ────────────────────────────────────────────────────

@receiver(post_save, sender='eval.EvalProject')
def on_project_save(sender, instance, **kwargs):
    """测评项目变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'project',
        'id': instance.id,
    })


@receiver(post_delete, sender='eval.EvalProject')
def on_project_delete(sender, instance, **kwargs):
    """测评项目删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'project',
    })


# ── OperationLog（审计日志）─────────────────────────────────────────

@receiver(post_save, sender='audit.OperationLog')
def on_audit_log_save(sender, instance, **kwargs):
    """操作日志新增时通知操作者 + 广播。"""
    if instance.user_id:
        _safe_publish(instance.user_id, {
            'type': 'data_changed',
            'model': 'audit_log',
            'id': instance.id,
        })
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'audit_log',
        'id': instance.id,
    })


# ── User ───────────────────────────────────────────────────────────

@receiver(post_save, sender='users.User')
def on_user_save(sender, instance, **kwargs):
    """用户信息变化时广播（用户管理列表刷新）。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'user',
        'id': instance.id,
    })


# ── Department ────────────────────────────────────────────────────

@receiver(post_save, sender='org.Department')
def on_department_save(sender, instance, **kwargs):
    """院系变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'department',
        'id': instance.id,
    })


@receiver(post_delete, sender='org.Department')
def on_department_delete(sender, instance, **kwargs):
    """院系删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'department',
    })


# ── Major ─────────────────────────────────────────────────────────

@receiver(post_save, sender='org.Major')
def on_major_save(sender, instance, **kwargs):
    """专业变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'major',
        'id': instance.id,
    })


@receiver(post_delete, sender='org.Major')
def on_major_delete(sender, instance, **kwargs):
    """专业删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'major',
    })


# ── Class ─────────────────────────────────────────────────────────

@receiver(post_save, sender='org.Class')
def on_class_save(sender, instance, **kwargs):
    """班级变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'class',
        'id': instance.id,
    })


@receiver(post_delete, sender='org.Class')
def on_class_delete(sender, instance, **kwargs):
    """班级删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'class',
    })


# ── EvalIndicator ─────────────────────────────────────────────────

@receiver(post_save, sender='eval.EvalIndicator')
def on_indicator_save(sender, instance, **kwargs):
    """测评指标变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'indicator',
        'id': instance.id,
    })


@receiver(post_delete, sender='eval.EvalIndicator')
def on_indicator_delete(sender, instance, **kwargs):
    """测评指标删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'indicator',
    })


# ── ScoreWeightRule ───────────────────────────────────────────────

@receiver(post_save, sender='eval.ScoreWeightRule')
def on_weight_rule_save(sender, instance, **kwargs):
    """权重规则变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'weight_rule',
        'id': instance.id,
    })


@receiver(post_delete, sender='eval.ScoreWeightRule')
def on_weight_rule_delete(sender, instance, **kwargs):
    """权重规则删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'weight_rule',
    })


# ── ReviewRule ────────────────────────────────────────────────────

@receiver(post_save, sender='eval.ReviewRule')
def on_review_rule_save(sender, instance, **kwargs):
    """评审规则变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'review_rule',
        'id': instance.id,
    })


@receiver(post_delete, sender='eval.ReviewRule')
def on_review_rule_delete(sender, instance, **kwargs):
    """评审规则删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'review_rule',
    })


# ── ReviewAssignment ──────────────────────────────────────────────

@receiver(post_save, sender='scoring.ReviewAssignment')
def on_review_assignment_save(sender, instance, **kwargs):
    """评审分配变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'review_assignment',
        'id': instance.id,
    })


@receiver(post_delete, sender='scoring.ReviewAssignment')
def on_review_assignment_delete(sender, instance, **kwargs):
    """评审分配删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'review_assignment',
    })


# ── LateSubmitChannel ─────────────────────────────────────────────

@receiver(post_save, sender='audit.LateSubmitChannel')
def on_late_channel_save(sender, instance, **kwargs):
    """补交通道变化时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'late_channel',
        'id': instance.id,
    })


@receiver(post_delete, sender='audit.LateSubmitChannel')
def on_late_channel_delete(sender, instance, **kwargs):
    """补交通道删除时广播。"""
    _safe_broadcast({
        'type': 'data_changed',
        'model': 'late_channel',
    })
