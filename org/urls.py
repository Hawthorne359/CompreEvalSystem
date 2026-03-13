"""
组织架构 URL。
"""
from django.urls import path
from . import views

urlpatterns = [
    # 院系列表（GET）、新建院系（POST）
    path('departments/', views.DepartmentListAPIView.as_view(), name='department-list'),
    path('departments/batch-delete/', views.DepartmentBatchDeleteAPIView.as_view(), name='department-batch-delete'),
    # 人员架构树：系主任 → 辅导员 → 学生助理
    path('departments/personnel-tree/', views.DepartmentPersonnelTreeAPIView.as_view(), name='department-personnel-tree'),
    # 院系详情（GET）、更新（PATCH）、删除（DELETE）
    path('departments/<int:pk>/', views.DepartmentDetailAPIView.as_view(), name='department-detail'),
    # 专业列表（GET）、新建专业（POST）
    path('majors/', views.MajorListAPIView.as_view(), name='major-list'),
    # 专业详情（GET）、更新（PATCH）、删除（DELETE）
    path('majors/<int:pk>/', views.MajorDetailAPIView.as_view(), name='major-detail'),
    # 班级列表（GET）、新建班级（POST）
    path('classes/', views.ClassListAPIView.as_view(), name='class-list'),
    path('classes/batch-delete/', views.ClassBatchDeleteAPIView.as_view(), name='class-batch-delete'),
    # 注意：<pk>/students/ 必须在 <pk>/ 之前，避免路由歧义
    path('classes/<int:pk>/students/', views.ClassStudentListAPIView.as_view(), name='class-students'),
    # 班级详情（GET）、更新（PATCH）、删除（DELETE）
    path('classes/<int:pk>/', views.ClassDetailAPIView.as_view(), name='class-detail'),
    # 扩展：某用户（辅导员等）负责的班级下的学生
    path('responsible-class-students/', views.ResponsibleClassStudentsAPIView.as_view(), name='responsible-class-students'),
]
