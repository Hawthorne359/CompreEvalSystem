"""
修复历史“未完成必需叶子指标却提前产出 final_score / approved”问题。
"""
from django.core.management.base import BaseCommand

from scoring.services import recompute_submission_final_score, submission_missing_required_leaf_indicators
from submission.models import StudentSubmission


class Command(BaseCommand):
    """批量扫描并可选修复提前出分数据。"""
    help = '扫描并修复提前出分/提前通过的数据（默认 dry-run）'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='执行写库修复（默认仅扫描）')
        parser.add_argument('--project-id', type=int, default=None, help='仅扫描指定项目')
        parser.add_argument(
            '--student-nos',
            type=str,
            default='',
            help='仅扫描指定学号（逗号分隔），例如 202284014037,202284014041',
        )
        parser.add_argument('--sample-limit', type=int, default=20, help='样本输出数量上限')

    def handle(self, *args, **options):
        apply_changes = bool(options.get('apply'))
        project_id = options.get('project_id')
        student_no_csv = (options.get('student_nos') or '').strip()
        sample_limit = max(int(options.get('sample_limit', 20)), 1)

        qs = StudentSubmission.objects.filter(final_score__isnull=False).select_related('project', 'user').order_by('id')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if student_no_csv:
            student_nos = [s.strip() for s in student_no_csv.split(',') if s.strip()]
            qs = qs.filter(user__student_no__in=student_nos)

        scanned = qs.count()
        candidates = []
        samples = []
        for sub in qs.iterator(chunk_size=300):
            missing = submission_missing_required_leaf_indicators(sub)
            if not missing:
                continue
            candidates.append(sub.id)
            if len(samples) < sample_limit:
                samples.append({
                    'submission_id': sub.id,
                    'student_no': getattr(sub.user, 'student_no', ''),
                    'project_id': sub.project_id,
                    'old_status': sub.status,
                    'old_final_score': str(sub.final_score),
                    'missing_count': len(missing),
                })

        fixed_count = 0
        if apply_changes:
            for sub in StudentSubmission.objects.filter(id__in=candidates).select_related('project', 'user'):
                recompute_submission_final_score(sub)
                sub.refresh_from_db(fields=['final_score', 'status'])
                if sub.status == 'approved' and sub.final_score is None:
                    sub.status = 'under_review'
                    sub.save(update_fields=['status'])
                fixed_count += 1

        mode = 'apply' if apply_changes else 'dry-run'
        self.stdout.write(
            self.style.SUCCESS(
                f'执行完成 mode={mode}, scanned={scanned}, candidate_count={len(candidates)}, fixed_count={fixed_count}'
            )
        )
        if samples:
            self.stdout.write(self.style.WARNING(f'样本: {samples}'))
