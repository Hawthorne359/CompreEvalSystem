"""
测评 URL（挂载在 api/v1/ 下）。
"""
from django.urls import path
from . import views

urlpatterns = [
    path('seasons/', views.SeasonListCreateView.as_view(), name='season-list'),
    path('seasons/batch-status/', views.SeasonBatchStatusView.as_view(), name='season-batch-status'),
    path('seasons/batch-delete/', views.SeasonBatchDeleteView.as_view(), name='season-batch-delete'),
    path('seasons/<int:pk>/', views.SeasonDetailView.as_view(), name='season-detail'),
    path('seasons/<int:pk>/delete/', views.SeasonDeleteView.as_view(), name='season-delete'),
    path('seasons/<int:season_id>/projects/', views.SeasonProjectListCreateView.as_view(), name='season-projects'),
    path('projects/batch-status/', views.ProjectBatchStatusView.as_view(), name='project-batch-status'),
    path('projects/batch-delete/', views.ProjectBatchDeleteView.as_view(), name='project-batch-delete'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    path('projects/<int:project_id>/indicators/', views.ProjectIndicatorListCreateView.as_view(), name='project-indicators'),
    path('projects/<int:project_id>/indicators/tree/', views.ProjectIndicatorTreeView.as_view(), name='project-indicators-tree'),
    path('projects/<int:project_id>/indicators/<int:pk>/', views.ProjectIndicatorDetailView.as_view(), name='project-indicator-detail'),
    path('projects/<int:project_id>/weight-rule/', views.ProjectWeightRuleView.as_view(), name='project-weight-rule'),
    path('projects/<int:project_id>/review-rule/', views.ProjectReviewRuleView.as_view(), name='project-review-rule'),
    path('projects/<int:project_id>/import-config/', views.ProjectImportConfigView.as_view(), name='project-import-config'),
    path('project-config-templates/', views.ProjectConfigTemplateListAPIView.as_view(), name='project-config-template-list'),
    path('projects/<int:project_id>/config-templates/save/', views.ProjectConfigTemplateSaveAPIView.as_view(), name='project-config-template-save'),
    path('projects/<int:project_id>/config-templates/<int:template_id>/apply/', views.ProjectConfigTemplateApplyAPIView.as_view(), name='project-config-template-apply'),
]
