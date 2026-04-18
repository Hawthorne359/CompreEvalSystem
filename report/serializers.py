"""
报表导出模板与映射序列化器。
"""
from rest_framework import serializers

from .models import ReportExportTemplate, ReportExportMapping, ReportExportFieldPreference
from .services import validate_export_mapping_config


class ReportExportTemplateSerializer(serializers.ModelSerializer):
    """导出模板序列化。"""

    owner_name = serializers.CharField(source='owner.name', read_only=True)

    class Meta:
        model = ReportExportTemplate
        fields = [
            'id',
            'name',
            'template_type',
            'project',
            'owner',
            'owner_name',
            'department',
            'visibility',
            'file',
            'is_active',
            'version',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['owner', 'owner_name', 'is_active', 'version', 'created_at', 'updated_at']


class ReportExportMappingSerializer(serializers.ModelSerializer):
    """导出映射序列化。"""

    owner_name = serializers.CharField(source='owner.name', read_only=True)

    class Meta:
        model = ReportExportMapping
        fields = [
            'id',
            'name',
            'project',
            'template',
            'owner',
            'owner_name',
            'output_format',
            'is_default',
            'config',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['owner', 'owner_name', 'created_at', 'updated_at']

    def validate(self, attrs):
        """保存前校验映射配置，避免导出时才报错。"""
        output_format = attrs.get('output_format')
        if output_format is None and self.instance is not None:
            output_format = self.instance.output_format
        config = attrs.get('config')
        if config is None and self.instance is not None:
            config = self.instance.config
        try:
            attrs['config'] = validate_export_mapping_config(config or {}, output_format=output_format or 'xlsx')
        except ValueError as exc:
            raise serializers.ValidationError({'config': str(exc)}) from exc
        return attrs


class ReportExportFieldPreferenceSerializer(serializers.ModelSerializer):
    """用户导出字段偏好序列化。"""

    class Meta:
        model = ReportExportFieldPreference
        fields = [
            'id',
            'user',
            'project',
            'common_field_keys',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'project', 'created_at', 'updated_at']

    def validate_common_field_keys(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('common_field_keys 必须为数组')
        cleaned = []
        seen = set()
        for item in value:
            key = str(item or '').strip()
            if not key:
                continue
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(key)
        return cleaned
