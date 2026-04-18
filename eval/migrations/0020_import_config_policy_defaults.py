from django.db import migrations


def fill_import_policy_defaults(apps, schema_editor):
    EvalProject = apps.get_model('eval', 'EvalProject')
    for project in EvalProject.objects.all().iterator():
        cfg = project.import_config or {}
        if not isinstance(cfg, dict):
            cfg = {}
        changed = False
        if 'import_mode' not in cfg:
            cfg['import_mode'] = 'subordinate_self'
            changed = True
        if 'subordinate_requires_approval' not in cfg:
            cfg['subordinate_requires_approval'] = True
            changed = True
        if changed:
            project.import_config = cfg
            project.save(update_fields=['import_config', 'updated_at'])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ('eval', '0019_alter_evalindicator_id_alter_evalproject_id_and_more'),
    ]

    operations = [
        migrations.RunPython(fill_import_policy_defaults, noop_reverse),
    ]
