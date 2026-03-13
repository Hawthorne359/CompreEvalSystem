"""
报表 URL。
"""
from django.urls import path
from . import views

urlpatterns = [
    path('report/project/<int:pk>/summary/', views.ReportProjectSummaryAPIView.as_view(), name='report-project-summary'),
    path('report/project/<int:pk>/ranking/', views.ReportProjectRankingAPIView.as_view(), name='report-project-ranking'),
    path('report/project/<int:pk>/export/', views.ReportProjectExportAPIView.as_view(), name='report-project-export'),
    path('report/project/<int:pk>/export/fields/', views.ReportExportFieldOptionsAPIView.as_view(), name='report-export-fields'),
    path('report/export/templates/', views.ReportExportTemplateListCreateAPIView.as_view(), name='report-export-template-list'),
    path('report/export/templates/<int:pk>/', views.ReportExportTemplateDetailAPIView.as_view(), name='report-export-template-detail'),
    path('report/export/mappings/', views.ReportExportMappingListCreateAPIView.as_view(), name='report-export-mapping-list'),
    path('report/export/mappings/<int:pk>/', views.ReportExportMappingDetailAPIView.as_view(), name='report-export-mapping-detail'),
    path('report/student/me/', views.ReportStudentMeAPIView.as_view(), name='report-student-me'),
    path('report/student/submissions/<int:pk>/detail/', views.ReportStudentSubmissionDetailAPIView.as_view(), name='report-student-submission-detail'),
]
