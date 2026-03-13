"""
院系、专业、班级序列化器。
"""
from rest_framework import serializers
from .models import Department, Major, Class
from users.serializers import UserListSerializer


class DepartmentSerializer(serializers.ModelSerializer):
    """院系。"""

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'parent', 'created_at', 'updated_at']


class DepartmentTreeSerializer(serializers.ModelSerializer):
    """院系树形（含子节点）。"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'parent', 'children']

    def get_children(self, obj):
        qs = obj.children.all()
        return DepartmentTreeSerializer(qs, many=True).data if qs.exists() else []


class MajorSerializer(serializers.ModelSerializer):
    """专业（含年级列表）。"""

    class Meta:
        model = Major
        fields = ['id', 'name', 'code', 'department', 'grades', 'created_at', 'updated_at']


class ClassSerializer(serializers.ModelSerializer):
    """班级。"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    major_name = serializers.CharField(source='major.name', read_only=True, allow_null=True)
    academic_year = serializers.CharField(source='current_academic_year', read_only=True)

    class Meta:
        model = Class
        fields = ['id', 'name', 'department', 'department_name', 'major', 'major_name', 'grade', 'academic_year', 'created_at', 'updated_at']


class ClassWithStudentsSerializer(ClassSerializer):
    """班级及其学生列表。"""
    students = serializers.SerializerMethodField()

    class Meta(ClassSerializer.Meta):
        fields = ClassSerializer.Meta.fields + ['students']

    def get_students(self, obj):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(class_obj=obj).order_by('student_no', 'username')
        return UserListSerializer(users, many=True).data
