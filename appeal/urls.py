"""
申诉 URL。
"""
from django.urls import path
from . import views

urlpatterns = [
    path('submissions/<int:pk>/appeal/', views.AppealCreateAPIView.as_view(), name='appeal-create'),
    path('appeals/', views.AppealListAPIView.as_view(), name='appeal-list'),
    path('appeals/<int:pk>/', views.AppealDetailAPIView.as_view(), name='appeal-detail'),
    path('appeals/<int:pk>/attachments/', views.AppealAttachmentUploadAPIView.as_view(), name='appeal-attachment-upload'),
    path('appeals/<int:pk>/attachments/<int:attachment_id>/', views.AppealAttachmentDeleteAPIView.as_view(), name='appeal-attachment-delete'),
    path('appeals/<int:pk>/handle/', views.AppealHandleAPIView.as_view(), name='appeal-handle'),
    path('appeals/<int:pk>/escalate-handle/', views.AppealEscalateHandleAPIView.as_view(), name='appeal-escalate-handle'),
    path('appeals/<int:pk>/admin-handle/', views.AppealAdminHandleAPIView.as_view(), name='appeal-admin-handle'),
]
