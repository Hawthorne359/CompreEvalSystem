"""
实时推送 URL 路由。
"""
from django.urls import path

from . import views

urlpatterns = [
    path('realtime/events/', views.sse_stream, name='realtime-events'),
]
