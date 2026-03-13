"""
API v1 聚合路由。
"""
from django.urls import path, include

urlpatterns = [
    path('', include('users.urls')),
    path('', include('org.urls')),
    path('', include('eval.urls')),
    path('', include('submission.urls')),
    path('', include('scoring.urls')),
    path('', include('appeal.urls')),
    path('', include('audit.urls')),
    path('', include('report.urls')),
    path('', include('dashboard.urls')),
    path('', include('realtime.urls')),
]
