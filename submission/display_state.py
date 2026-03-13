"""
提交展示状态统一计算。
"""


STATUS_LABEL_MAP = {
    'draft': '草稿',
    'submitted': '已提交',
    'under_review': '审核中',
    'approved': '已审核',
    'rejected': '已驳回',
    'appealing': '申诉中',
}

STATUS_TONE_MAP = {
    'draft': 'neutral',
    'submitted': 'info',
    'under_review': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'appealing': 'purple',
}


def derive_submission_display_state(status, is_arbitrated=False):
    """
    统一派生提交展示状态（不以 final_score 驱动，避免与流程态冲突）。
    @param status {str|None}
    @param is_arbitrated {bool}
    @returns {tuple[str, str]} (display_status, display_tone)
    """
    if is_arbitrated:
        return '已仲裁', 'purple'
    normalized_status = status or ''
    return (
        STATUS_LABEL_MAP.get(normalized_status, normalized_status or '未知状态'),
        STATUS_TONE_MAP.get(normalized_status, 'neutral'),
    )
