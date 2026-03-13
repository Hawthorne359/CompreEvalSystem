"""
工作台 URL。
"""
from django.urls import path
from .views import DashboardAPIView, MissingSubmissionListAPIView

urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('dashboard/missing-list/', MissingSubmissionListAPIView.as_view(), name='dashboard-missing-list'),
]
