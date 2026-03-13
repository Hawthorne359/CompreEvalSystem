"""
审计日志与补交通道 Django Admin 配置。

设计原则：
- OperationLog 全字段只读（禁止手动增改），支持多维搜索和过滤，提供 CSV 导出 action。
- AuditAttachment 只读展示，通过 OperationLog 的 inline 访问。
- LateSubmitRequest 只读，显示学生信息、申请状态、来源区分。
- LateSubmitChannel 只读，显示开启来源（学生申请 / 管理员手动）、范围、目标、状态。
"""
import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import localtime
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import OperationLog, AuditAttachment, LateSubmitRequest, LateSubmitChannel
from .serializers import ACTION_LABELS, LEVEL_LABELS, MODULE_LABELS


# ---------------------------------------------------------------------------
# OperationLog
# ---------------------------------------------------------------------------
class AuditAttachmentInline(admin.TabularInline):
    """在 OperationLog 详情页内嵌显示佐证附件。"""
    model = AuditAttachment
    extra = 0
    readonly_fields = ['file_name', 'file_size', 'content_type', 'file_link', 'uploaded_by', 'created_at']
    fields = ['file_name', 'file_size', 'content_type', 'file_link', 'uploaded_by', 'created_at']

    def file_link(self, obj):
        """附件下载链接。"""
        if obj.file:
            return format_html('<a href="{}" target="_blank">下载</a>', obj.file.url)
        return '—'
    file_link.short_description = '文件链接'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    """操作日志管理（只读）。"""
    list_display = [
        'id', 'created_at_display', 'level_badge', 'module_label',
        'action_label', 'username_snapshot', 'role_snapshot',
        'target_repr', 'ip_display', 'abnormal_badge', 'audit_badge',
    ]
    list_filter = [
        'level', 'module', 'is_abnormal', 'is_audit_event',
    ]
    search_fields = [
        'username_snapshot', 'role_snapshot', 'action',
        'target_repr', 'reason', 'ip_address',
    ]
    ordering = ['-created_at']
    inlines = [AuditAttachmentInline]
    actions = ['export_as_csv']

    readonly_fields = [
        'user', 'username_snapshot', 'role_snapshot',
        'ip_address', 'external_ip', 'user_agent',
        'module', 'action', 'level',
        'target_type', 'target_id', 'target_repr',
        'extra', 'reason',
        'is_abnormal', 'is_audit_event',
        'created_at',
    ]

    fieldsets = [
        ('操作者', {
            'fields': ['user', 'username_snapshot', 'role_snapshot'],
        }),
        ('网络信息', {
            'fields': ['ip_address', 'external_ip', 'user_agent'],
            'classes': ['collapse'],
        }),
        ('操作分类', {
            'fields': ['level', 'module', 'action'],
        }),
        ('操作对象', {
            'fields': ['target_type', 'target_id', 'target_repr'],
        }),
        ('详细内容', {
            'fields': ['reason', 'extra'],
        }),
        ('标记', {
            'fields': ['is_abnormal', 'is_audit_event', 'created_at'],
        }),
    ]

    def created_at_display(self, obj):
        """格式化时间到秒（转北京时间）。"""
        return localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = '操作时间'
    created_at_display.admin_order_field = 'created_at'

    def ip_display(self, obj):
        """仅展示外网 IP。"""
        return obj.external_ip or '—'
    ip_display.short_description = 'IP 地址'

    def level_badge(self, obj):
        """等级彩色徽章。"""
        colors = {
            OperationLog.LEVEL_INFO:     '#64748b',
            OperationLog.LEVEL_NOTICE:   '#0284c7',
            OperationLog.LEVEL_WARNING:  '#d97706',
            OperationLog.LEVEL_CRITICAL: '#b91c1c',
        }
        color = colors.get(obj.level, '#64748b')
        label = LEVEL_LABELS.get(obj.level, obj.level)
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, label,
        )
    level_badge.short_description = '等级'

    def module_label(self, obj):
        """模块中文名。"""
        return MODULE_LABELS.get(obj.module, obj.module)
    module_label.short_description = '模块'

    def action_label(self, obj):
        """操作中文名。"""
        return ACTION_LABELS.get(obj.action, obj.action)
    action_label.short_description = '操作'

    def abnormal_badge(self, obj):
        """异常状态徽章。"""
        if obj.is_abnormal:
            return mark_safe('<span style="color:#b91c1c;font-weight:600;">⚠ 异常</span>')
        return mark_safe('<span style="color:#15803d;">正常</span>')
    abnormal_badge.short_description = '异常'

    def audit_badge(self, obj):
        """审计事件标记。"""
        if obj.is_audit_event:
            return mark_safe('<span style="color:#7c3aed;font-weight:600;">📋 审计</span>')
        return '—'
    audit_badge.short_description = '审计事件'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description='导出选中日志为 CSV')
    def export_as_csv(self, request, queryset):
        """将选中的操作日志导出为 UTF-8 BOM CSV 文件（Excel 直接打开不乱码）。"""
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = (
            f'attachment; filename="oplog_{timezone.now():%Y%m%d_%H%M%S}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow([
            'ID', '操作时间', '等级', '模块', '操作', '用户名', '角色',
            '内网IP', '外网IP', '目标类型', '目标ID', '目标描述', '理由', '异常', '审计事件',
        ])
        for log in queryset.order_by('-created_at'):
            writer.writerow([
                log.id,
                localtime(log.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                LEVEL_LABELS.get(log.level, log.level),
                MODULE_LABELS.get(log.module, log.module),
                ACTION_LABELS.get(log.action, log.action),
                log.username_snapshot,
                log.role_snapshot,
                log.ip_address or '',
                log.external_ip or '',
                log.target_type,
                log.target_id or '',
                log.target_repr,
                log.reason,
                '是' if log.is_abnormal else '否',
                '是' if log.is_audit_event else '否',
            ])
        return response


# ---------------------------------------------------------------------------
# AuditAttachment
# ---------------------------------------------------------------------------
@admin.register(AuditAttachment)
class AuditAttachmentAdmin(admin.ModelAdmin):
    """审计附件管理（只读）。"""
    list_display = ['id', 'file_name', 'file_size', 'content_type', 'uploaded_by', 'operation_log_link', 'created_at']
    search_fields = ['file_name', 'uploaded_by__username']
    readonly_fields = ['operation_log', 'file', 'file_name', 'file_size', 'content_type', 'uploaded_by', 'created_at']
    ordering = ['-created_at']

    def operation_log_link(self, obj):
        """跳转到关联操作日志的链接。"""
        if obj.operation_log_id:
            url = reverse('admin:audit_operationlog_change', args=[obj.operation_log_id])
            return format_html('<a href="{}">日志#{}</a>', url, obj.operation_log_id)
        return '—'
    operation_log_link.short_description = '关联日志'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# LateSubmitRequest（学生补交申请）
# ---------------------------------------------------------------------------
@admin.register(LateSubmitRequest)
class LateSubmitRequestAdmin(admin.ModelAdmin):
    """
    学生补交申请管理（只读）。
    来源：由学生在提交详情页点击「申请补交」产生，区别于管理员直接开启的通道。
    """
    list_display = [
        'id', 'student_info', 'project_info', 'reason_short',
        'status_badge', 'has_channel_badge', 'handler_display', 'created_at_display',
    ]
    list_filter = ['status']
    search_fields = [
        'submission__user__username',
        'submission__user__student_no',
        'submission__project__name',
        'reason',
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'submission', 'reason', 'status', 'handler', 'handle_comment',
        'channel_link', 'created_at', 'updated_at',
    ]
    fieldsets = [
        ('申请信息', {
            'fields': ['submission', 'reason', 'status'],
        }),
        ('处理结果', {
            'fields': ['handler', 'handle_comment', 'channel_link'],
        }),
        ('时间', {
            'fields': ['created_at', 'updated_at'],
        }),
    ]

    def student_info(self, obj):
        """学生姓名 + 学号（双行）。"""
        u = obj.submission.user
        name = u.get_full_name() or u.username
        return mark_safe(f'<strong>{name}</strong><br><span style="color:#64748b;font-size:11px;">{u.student_no or u.username}</span>')
    student_info.short_description = '学生'

    def project_info(self, obj):
        """项目名称（截断）。"""
        name = obj.submission.project.name
        return name[:30] + '…' if len(name) > 30 else name
    project_info.short_description = '测评项目'

    def reason_short(self, obj):
        """申请理由截断。"""
        return obj.reason[:40] + '…' if len(obj.reason) > 40 else obj.reason
    reason_short.short_description = '申请理由'

    def status_badge(self, obj):
        """状态彩色徽章。"""
        colors = {
            LateSubmitRequest.STATUS_PENDING:  ('#d97706', '待审核'),
            LateSubmitRequest.STATUS_APPROVED: ('#15803d', '已批准'),
            LateSubmitRequest.STATUS_REJECTED: ('#b91c1c', '已拒绝'),
        }
        color, label = colors.get(obj.status, ('#64748b', obj.status))
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, label)
    status_badge.short_description = '状态'

    def has_channel_badge(self, obj):
        """是否已开启补交通道。"""
        has = hasattr(obj, 'channel') and obj.channel is not None
        if has:
            url = reverse('admin:audit_latesubmitchannel_change', args=[obj.channel.id])
            return format_html('<a href="{}" style="color:#0284c7;">通道#{}</a>', url, obj.channel.id)
        return mark_safe('<span style="color:#94a3b8;">未开启</span>')
    has_channel_badge.short_description = '补交通道'

    def handler_display(self, obj):
        """处理人用户名。"""
        return obj.handler.username if obj.handler else '—'
    handler_display.short_description = '处理人'

    def created_at_display(self, obj):
        """申请时间格式化（转北京时间）。"""
        return localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = '申请时间'
    created_at_display.admin_order_field = 'created_at'

    def channel_link(self, obj):
        """详情页内跳转到关联通道。"""
        if hasattr(obj, 'channel') and obj.channel:
            url = reverse('admin:audit_latesubmitchannel_change', args=[obj.channel.id])
            return format_html('<a href="{}">补交通道#{}</a>', url, obj.channel.id)
        return '—'
    channel_link.short_description = '关联补交通道'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# LateSubmitChannel（管理员开启的补交通道）
# ---------------------------------------------------------------------------
@admin.register(LateSubmitChannel)
class LateSubmitChannelAdmin(admin.ModelAdmin):
    """
    补交通道管理（只读）。
    通道来源：
      - 「来自学生申请」：from_request 不为空，表示管理员审批学生申请后自动创建
      - 「管理员手动开启」：from_request 为空，表示管理员主动在后台/前端开启
    """
    list_display = [
        'id', 'source_badge', 'scope_badge', 'target_display',
        'project_display', 'reason_short', 'duration_hours',
        'open_at_display', 'planned_close_at_display',
        'status_badge', 'opened_by_display',
    ]
    list_filter = ['scope_type', 'is_active', 'close_reason']
    search_fields = [
        'target_user__username', 'target_user__student_no',
        'target_class__name', 'opened_by__username', 'reason',
    ]
    ordering = ['-open_at']
    readonly_fields = [
        'opened_by', 'scope_type', 'target_user', 'target_class', 'project',
        'reason', 'duration_hours', 'open_at', 'planned_close_at',
        'actual_close_at', 'closed_by', 'close_reason', 'is_active',
        'from_request', 'request_link',
    ]
    fieldsets = [
        ('来源', {
            'fields': ['opened_by', 'from_request', 'request_link'],
            'description': '「来源申请」有值表示由学生申请审批产生；为空表示管理员手动开启',
        }),
        ('范围', {
            'fields': ['scope_type', 'target_user', 'target_class', 'project'],
        }),
        ('配置', {
            'fields': ['reason', 'duration_hours'],
        }),
        ('时间与状态', {
            'fields': ['open_at', 'planned_close_at', 'actual_close_at', 'closed_by', 'close_reason', 'is_active'],
        }),
    ]

    def source_badge(self, obj):
        """开启来源：学生申请 / 管理员手动。"""
        if obj.from_request_id:
            return format_html(
                '<span style="color:#7c3aed;font-weight:600;">学生申请</span>'
                '<br><span style="font-size:11px;color:#94a3b8;">申请#{}</span>',
                obj.from_request_id,
            )
        return mark_safe('<span style="color:#0284c7;font-weight:600;">管理员开启</span>')
    source_badge.short_description = '来源'

    def scope_badge(self, obj):
        """范围类型徽章。"""
        if obj.scope_type == LateSubmitChannel.SCOPE_USER:
            return mark_safe('<span style="background:#dbeafe;color:#1d4ed8;padding:2px 6px;border-radius:4px;font-size:11px;">个人</span>')
        return mark_safe('<span style="background:#ede9fe;color:#6d28d9;padding:2px 6px;border-radius:4px;font-size:11px;">班级</span>')
    scope_badge.short_description = '范围'

    def target_display(self, obj):
        """目标用户或班级信息。"""
        if obj.scope_type == LateSubmitChannel.SCOPE_USER and obj.target_user:
            u = obj.target_user
            name = u.get_full_name() or u.username
            return mark_safe(f'<strong>{name}</strong><br><span style="color:#64748b;font-size:11px;">{u.student_no or u.username}</span>')
        if obj.scope_type == LateSubmitChannel.SCOPE_CLASS and obj.target_class:
            return obj.target_class.name
        return '—'
    target_display.short_description = '目标'

    def project_display(self, obj):
        """限定项目名（无则显示"全部"）。"""
        return obj.project.name if obj.project else mark_safe('<span style="color:#94a3b8;">不限项目</span>')
    project_display.short_description = '限定项目'

    def reason_short(self, obj):
        """理由截断。"""
        return obj.reason[:35] + '…' if len(obj.reason) > 35 else obj.reason
    reason_short.short_description = '开启理由'

    def open_at_display(self, obj):
        """开启时间格式化（转北京时间）。"""
        return localtime(obj.open_at).strftime('%Y-%m-%d %H:%M:%S')
    open_at_display.short_description = '开启时间'
    open_at_display.admin_order_field = 'open_at'

    def planned_close_at_display(self, obj):
        """计划关闭时间格式化（转北京时间）。"""
        return localtime(obj.planned_close_at).strftime('%Y-%m-%d %H:%M:%S') if obj.planned_close_at else '—'
    planned_close_at_display.short_description = '计划关闭'

    def status_badge(self, obj):
        """通道状态徽章（激活中 / 已关闭原因 + 实际关闭时间）。"""
        if obj.is_active:
            now = timezone.now()
            if obj.planned_close_at and now < obj.planned_close_at:
                diff = obj.planned_close_at - now
                h = int(diff.total_seconds() // 3600)
                m = int((diff.total_seconds() % 3600) // 60)
                remaining = f'{h}h {m}m' if h else f'{m}m'
                return mark_safe(f'<span style="color:#15803d;font-weight:600;">激活中</span><br><span style="font-size:11px;color:#64748b;">剩余 {remaining}</span>')
            return mark_safe('<span style="color:#d97706;font-weight:600;">已过期（待清理）</span>')
        reason_map = {
            LateSubmitChannel.CLOSE_AUTO_EXPIRE: '自动到期',
            LateSubmitChannel.CLOSE_SUBMITTED:   '学生已提交',
            LateSubmitChannel.CLOSE_MANUAL:      '手动关闭',
        }
        reason = reason_map.get(obj.close_reason, obj.close_reason or '—')
        # 使用 localtime() 将 UTC 实际关闭时间转换为北京时间
        close_time = localtime(obj.actual_close_at).strftime('%Y-%m-%d %H:%M') if obj.actual_close_at else ''
        close_time_html = f'<br><span style="font-size:11px;color:#94a3b8;">关闭于 {close_time}</span>' if close_time else ''
        return mark_safe(
            f'<span style="color:#6b7280;">已关闭</span>'
            f'<br><span style="font-size:11px;color:#94a3b8;">{reason}</span>'
            f'{close_time_html}'
        )
    status_badge.short_description = '状态'

    def opened_by_display(self, obj):
        """开启者用户名。"""
        return obj.opened_by.username if obj.opened_by else '—'
    opened_by_display.short_description = '开启者'

    def request_link(self, obj):
        """详情页内跳转到来源申请。"""
        if obj.from_request_id:
            url = reverse('admin:audit_latesubmitrequest_change', args=[obj.from_request_id])
            return format_html('<a href="{}">补交申请#{}</a>', url, obj.from_request_id)
        return '管理员手动开启（无关联申请）'
    request_link.short_description = '来源申请'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
