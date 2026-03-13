"""
学生提交 URL。
"""
from django.urls import path
from . import views

urlpatterns = [
    path('submission-tasks/', views.SubmissionTaskListAPIView.as_view(), name='submission-task-list'),
    path('submissions/', views.SubmissionListCreateView.as_view(), name='submission-list'),
    path('submissions/<int:pk>/', views.SubmissionDetailView.as_view(), name='submission-detail'),
    path('submissions/<int:pk>/questions/', views.SubmissionQuestionListView.as_view(), name='submission-questions'),
    path('submissions/<int:pk>/questions/<int:indicator_id>/', views.SubmissionQuestionSaveView.as_view(), name='submission-question-save'),
    path('submissions/<int:pk>/submit/', views.SubmissionSubmitView.as_view(), name='submission-submit'),
    path('submissions/<int:pk>/evidences/', views.EvidenceUploadView.as_view(), name='submission-evidences'),
    path('submissions/<int:pk>/evidences/<int:evidence_id>/', views.EvidenceDeleteView.as_view(), name='submission-evidence-delete'),
]
