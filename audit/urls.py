"""
审计与补交通道 URL。
"""
from django.urls import path
from . import views

urlpatterns = [
    # 超级管理员操作日志（仅返回其自己的记录，全量日志请通过 Django admin 查询）
    path('audit/logs/', views.OperationLogListAPIView.as_view(), name='audit-logs'),
    path('audit/logs/export/', views.OperationLogExportAPIView.as_view(), name='audit-logs-export'),
    path('audit/logs/<int:pk>/', views.OperationLogDetailAPIView.as_view(), name='audit-log-detail'),
    # 个人操作日志（所有已登录用户，只能查看自己的记录）
    path('audit/my-logs/', views.MyOperationLogListAPIView.as_view(), name='my-audit-logs'),
    path('audit/my-logs/<int:pk>/', views.MyOperationLogDetailAPIView.as_view(), name='my-audit-log-detail'),
    # 高危操作
    path('admin/score-override/', views.ScoreOverrideAPIView.as_view(), name='admin-score-override'),
    # 补交申请（学生端，挂在 submissions/<id>/ 下）
    path('submissions/<int:submission_id>/late-request/', views.LateRequestCreateView.as_view(), name='late-request-create'),
    path('submissions/<int:submission_id>/late-status/', views.LateStatusView.as_view(), name='late-status'),
    # 补交通道管理（管理员端）
    path('admin/late-requests/', views.LateRequestListView.as_view(), name='admin-late-requests'),
    path('admin/late-requests/<int:pk>/handle/', views.LateRequestHandleView.as_view(), name='admin-late-request-handle'),
    path('admin/late-channels/', views.LateChannelListCreateView.as_view(), name='admin-late-channels'),
    path('admin/late-channels/<int:pk>/close/', views.LateChannelCloseView.as_view(), name='admin-late-channel-close'),
    path('admin/late-submissions/pending/', views.LatePendingSubmissionListView.as_view(), name='admin-late-pending-submissions'),
    path('admin/late-submissions/batch-push/', views.LatePendingSubmissionBatchPushView.as_view(), name='admin-late-pending-submissions-batch-push'),
]
