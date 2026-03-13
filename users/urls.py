"""
用户与认证 URL。
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'roles', views.RoleViewSet, basename='role')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('auth/login/', views.AuthLoginView.as_view(), name='auth-login'),
    path('auth/refresh/', views.AuthRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', views.AuthLogoutView.as_view(), name='auth-logout'),
    path('auth/switch-role/', views.AuthSwitchRoleView.as_view(), name='auth-switch-role'),
    path('auth/verify-password/', views.VerifyPasswordView.as_view(), name='auth-verify-password'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    path('users/me/', views.CurrentUserView.as_view(), name='users-me'),
    path('users/me/login-history/', views.LoginHistoryView.as_view(), name='users-me-login-history'),
    path('users/me/profile/', views.UpdateProfileView.as_view(), name='users-me-profile'),
    path('users/import/', views.UserImportAPIView.as_view(), name='users-import'),
    path('users/import/template/', views.UserImportTemplateAPIView.as_view(), name='users-import-template'),
    path('users/import/progress/<int:batch_id>/', views.ImportProgressView.as_view(), name='users-import-progress'),
    path('', include(router.urls)),
]
