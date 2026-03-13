"""
审核与评分 URL。
"""
from django.urls import path
from . import views

urlpatterns = [
    path('review/tasks/', views.ReviewTaskListAPIView.as_view(), name='review-tasks'),
    path('review/assignments/generate/', views.ReviewAssignmentGenerateAPIView.as_view(), name='review-assign-generate'),
    path('review/assignments/release/', views.CounselorAssignmentReleaseAPIView.as_view(), name='review-assign-release'),
    path('review/assignments/my/', views.MyReviewAssignmentsAPIView.as_view(), name='review-assign-my'),
    path('review/assignments/summary/', views.ProjectReviewAssignmentSummaryAPIView.as_view(), name='review-assign-summary'),
    path('review/submissions/<int:pk>/', views.ReviewSubmissionDetailAPIView.as_view(), name='review-submission-detail'),
    path('review/submissions/<int:pk>/questions/', views.ReviewQuestionListAPIView.as_view(), name='review-submission-questions'),
    path('review/submissions/<int:pk>/objections/', views.ReviewObjectionCreateAPIView.as_view(), name='review-objection-create'),
    path('review/submissions/<int:pk>/initial/', views.ReviewInitialAPIView.as_view(), name='review-initial'),
    path('review/submissions/<int:pk>/scores/', views.ReviewScoresListCreateAPIView.as_view(), name='review-scores'),
    path('review/submissions/<int:pk>/arbitrate/', views.ReviewArbitrateAPIView.as_view(), name='review-arbitrate'),
    path('review/submissions/<int:pk>/batch-arbitrate/', views.ReviewBatchArbitrateAPIView.as_view(), name='review-batch-arbitrate'),
    path('review/objections/', views.ReviewObjectionListAPIView.as_view(), name='review-objection-list'),
    path('review/objections/<int:pk>/', views.ReviewObjectionDetailAPIView.as_view(), name='review-objection-detail'),
    path('review/objections/<int:pk>/handle/', views.ReviewObjectionHandleAPIView.as_view(), name='review-objection-handle'),
    path('review/objections/<int:pk>/attachments/', views.ReviewObjectionAttachmentUploadAPIView.as_view(), name='review-objection-attachment-upload'),
    path('review/objections/<int:pk>/attachments/<int:attachment_id>/', views.ReviewObjectionAttachmentDeleteAPIView.as_view(), name='review-objection-attachment-delete'),
    # 学生助理（评卷助理）接口
    path('review/assistant/list/', views.AssistantListAPIView.as_view(), name='assistant-list'),
    path('review/assistant/assign/', views.AssistantAssignAPIView.as_view(), name='assistant-assign'),
    path('review/assistant/revoke/', views.AssistantRevokeAPIView.as_view(), name='assistant-revoke'),
    path('review/assistant-tasks/', views.AssistantTaskListAPIView.as_view(), name='assistant-tasks'),
    path('review/assistant-tasks/<int:pk>/score/', views.AssistantScoreAPIView.as_view(), name='assistant-score'),
    path('scoring/import/', views.ScoringImportAPIView.as_view(), name='scoring-import'),
    path('scoring/import/precheck/', views.ScoringImportPrecheckAPIView.as_view(), name='scoring-import-precheck'),
    path('scoring/import/template/', views.ScoringImportTemplateAPIView.as_view(), name='scoring-import-template'),
]
