"""
提交模块权限：本人或审核链（level >= 2）可读。
"""
from rest_framework.permissions import BasePermission


class IsSubmissionOwnerOrReviewer(BasePermission):
    """
    本人可读写自己的提交；
    评审老师（辅导员）及以上（level >= 2）可读任意提交（审核链）。
    学生助理（level == 1）通过专用助理接口访问，不在此处开放。
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if obj.user_id == request.user.id:
            return True
        from users.permissions import user_level_at_least
        return user_level_at_least(request.user, 2)
