"""
操作日志写入服务，供全系统各模块调用。

使用示例
--------
普通操作::

    from audit.services import log_action
    from audit.models import OperationLog

    log_action(
        user=request.user,
        action='season_create',
        module=OperationLog.MODULE_EVAL,
        level=OperationLog.LEVEL_WARNING,
        target_type='eval_season',
        target_id=season.id,
        target_repr=season.name,
        request=request,
    )

含附件的高危操作（如改分、开补交通道）::

    from audit.services import log_action_with_attachment

    log_action_with_attachment(
        user=request.user,
        action='score_override',
        module=OperationLog.MODULE_SCORING,
        level=OperationLog.LEVEL_CRITICAL,
        target_type='submission',
        target_id=sub.id,
        target_repr=str(sub.id),
        reason=reason,
        extra={'old_score': str(old_score), 'new_score': str(new_score)},
        file_obj=request.FILES.get('evidence_file'),
        is_audit_event=True,
        is_abnormal=True,
        request=request,
    )
"""
import threading

from .models import OperationLog, AuditAttachment

# thread-local 存储由 RequestLogMiddleware 写入的请求元信息
_request_local = threading.local()


def _get_ip(request=None):
    """从 request 或 thread-local 获取内网（局域网）IP。"""
    if request is not None:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    return getattr(_request_local, 'ip_address', None)


def _get_external_ip(request=None):
    """从 request 或 thread-local 获取客户端上报的公网 IP。"""
    if request is not None:
        return request.META.get('HTTP_X_CLIENT_PUBLIC_IP', '').strip() or None
    return getattr(_request_local, 'external_ip', None)


def _get_ua(request=None):
    """从 request 或 thread-local 获取 User-Agent。"""
    if request is not None:
        return request.META.get('HTTP_USER_AGENT', '')[:500]
    return getattr(_request_local, 'user_agent', '')


def _get_role_snapshot(user):
    """返回用户当前角色名称快照，无角色时返回空字符串。"""
    if user is None:
        return ''
    role = getattr(user, 'current_role', None)
    if role is None:
        return ''
    return getattr(role, 'name', '') or ''


def log_action(
    user,
    action,
    module,
    level=OperationLog.LEVEL_INFO,
    target_type='',
    target_id=None,
    target_repr='',
    extra=None,
    reason='',
    is_abnormal=False,
    is_audit_event=False,
    request=None,
):
    """
    写入一条操作日志。

    Parameters
    ----------
    user : User | None
        操作者，可为 None（如匿名登录失败）。
    action : str
        操作码，如 ``login`` / ``create_season`` / ``delete_project``。
    module : str
        业务模块，使用 ``OperationLog.MODULE_*`` 常量。
    level : str
        日志等级，使用 ``OperationLog.LEVEL_*`` 常量，默认 INFO。
    target_type : str
        操作对象类型，如 ``eval_season``。
    target_id : int | None
        操作对象主键。
    target_repr : str
        操作对象的可读描述，如 ``"2024-2025学年春季"``。
    extra : dict | None
        附加上下文，如旧值/新值。
    reason : str
        操作理由，WARNING/CRITICAL 级必填。
    is_abnormal : bool
        是否标记为异常操作。
    is_audit_event : bool
        是否为正式审计事件（在前端"审计日志"视图中展示）。
    request : HttpRequest | None
        Django 请求对象，用于自动提取 IP 和 User-Agent；
        若不传则从 thread-local 读取（由 RequestLogMiddleware 写入）。

    Returns
    -------
    OperationLog
    """
    username_snapshot = ''
    if user is not None:
        username_snapshot = getattr(user, 'username', '') or ''

    return OperationLog.objects.create(
        user=user,
        username_snapshot=username_snapshot,
        role_snapshot=_get_role_snapshot(user),
        ip_address=_get_ip(request) or None,
        external_ip=_get_external_ip(request),
        user_agent=_get_ua(request),
        module=module,
        action=action,
        level=level,
        target_type=target_type,
        target_id=target_id,
        target_repr=target_repr,
        extra=extra or {},
        reason=reason,
        is_abnormal=is_abnormal,
        is_audit_event=is_audit_event,
    )


def log_action_with_attachment(
    user,
    action,
    module,
    level=OperationLog.LEVEL_CRITICAL,
    target_type='',
    target_id=None,
    target_repr='',
    extra=None,
    reason='',
    is_abnormal=False,
    is_audit_event=True,
    request=None,
    file_obj=None,
):
    """
    写入一条操作日志并（可选）保存佐证附件。

    Parameters
    ----------
    file_obj : InMemoryUploadedFile | TemporaryUploadedFile | None
        Django 上传文件对象，若为 None 则只写日志不写附件。

    Returns
    -------
    tuple[OperationLog, AuditAttachment | None]
    """
    op_log = log_action(
        user=user,
        action=action,
        module=module,
        level=level,
        target_type=target_type,
        target_id=target_id,
        target_repr=target_repr,
        extra=extra,
        reason=reason,
        is_abnormal=is_abnormal,
        is_audit_event=is_audit_event,
        request=request,
    )

    attachment = None
    if file_obj is not None:
        attachment = AuditAttachment.objects.create(
            operation_log=op_log,
            file=file_obj,
            file_name=getattr(file_obj, 'name', ''),
            file_size=getattr(file_obj, 'size', 0),
            content_type=getattr(file_obj, 'content_type', ''),
            uploaded_by=user,
        )

    return op_log, attachment
