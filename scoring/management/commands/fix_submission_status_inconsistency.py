"""
修复历史提交状态异常：
- status 为 submitted/under_review，但 final_score 已存在且无待完成常规评审任务
"""
from django.core.management.base import BaseCommand

from audit.models import OperationLog
from audit.services import log_action
from scoring.models import ReviewAssignment
from submission.models import StudentSubmission


class Command(BaseCommand):
    help = '扫描并可选修复提交状态与评分闭环不一致问题（默认 dry-run）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='执行修复（默认仅扫描，不写库）',
        )
        parser.add_argument(
            '--sample-limit',
            type=int,
            default=20,
            help='输出样本条数上限',
        )

    def handle(self, *args, **options):
        apply_changes = bool(options.get('apply'))
        sample_limit = max(int(options.get('sample_limit', 20)), 1)

        suspect_qs = StudentSubmission.objects.filter(
            status__in=['submitted', 'under_review'],
            final_score__isnull=False,
        ).select_related('project', 'user').order_by('id')

        scanned = suspect_qs.count()
        candidate_ids = []
        samples = []

        for sub in suspect_qs.iterator(chunk_size=300):
            has_pending_assignment = ReviewAssignment.objects.filter(
                submission=sub,
                status='assigned',
                role_type__in=['assistant', 'counselor', 'counselor_confirm'],
            ).exists()
            if has_pending_assignment:
                continue
            candidate_ids.append(sub.id)
            if len(samples) < sample_limit:
                samples.append({
                    'submission_id': sub.id,
                    'student_no': getattr(sub.user, 'student_no', ''),
                    'project_id': sub.project_id,
                    'old_status': sub.status,
                    'final_score': str(sub.final_score),
                })

        fixed_count = 0
        if apply_changes and candidate_ids:
            fixed_count = StudentSubmission.objects.filter(id__in=candidate_ids).update(status='approved')

        summary = {
            'dry_run': not apply_changes,
            'scanned': scanned,
            'candidate_count': len(candidate_ids),
            'fixed_count': fixed_count,
            'samples': samples,
        }

        if apply_changes and fixed_count > 0:
            log_action(
                user=None,
                action='submission_status_consistency_fix',
                module=OperationLog.MODULE_SCORING,
                level=OperationLog.LEVEL_WARNING,
                target_type='submission',
                target_id=0,
                target_repr='submission_status_consistency_fix',
                extra=summary,
                reason='修复提交状态与评分闭环不一致',
                is_audit_event=True,
                is_abnormal=False,
                request=None,
            )

        mode_text = 'apply' if apply_changes else 'dry-run'
        self.stdout.write(
            self.style.SUCCESS(
                f'执行完成 mode={mode_text}, scanned={scanned}, candidate_count={len(candidate_ids)}, fixed_count={fixed_count}'
            )
        )
