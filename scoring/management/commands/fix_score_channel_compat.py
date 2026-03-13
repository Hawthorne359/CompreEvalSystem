"""
修复历史 score_channel 兼容问题：
- 识别 indicator.score_source='import' 但 score_channel='assignment' 的历史记录
- 可选回填为 score_channel='import'
"""
from django.core.management.base import BaseCommand

from audit.models import OperationLog
from audit.services import log_action
from scoring.models import ScoreRecord


class Command(BaseCommand):
    help = '扫描并可选修复历史 score_channel 异常记录（默认 dry-run）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='执行回填（默认仅扫描，不写库）',
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

        suspect_qs = ScoreRecord.objects.filter(
            score_channel='assignment',
            indicator__score_source='import',
        ).select_related('indicator', 'submission', 'reviewer').order_by('id')

        total_suspects = suspect_qs.count()
        fixed_count = 0
        samples = []

        for rec in suspect_qs.iterator(chunk_size=500):
            if len(samples) < sample_limit:
                samples.append({
                    'score_record_id': rec.id,
                    'submission_id': rec.submission_id,
                    'indicator_id': rec.indicator_id,
                    'indicator_score_source': rec.indicator.score_source,
                    'round_type': rec.round_type,
                    'old_score_channel': rec.score_channel,
                    'reviewer_id': rec.reviewer_id,
                })
            if apply_changes:
                rec.score_channel = 'import'
                rec.save(update_fields=['score_channel'])
                fixed_count += 1

        summary = {
            'dry_run': not apply_changes,
            'total_suspects': total_suspects,
            'fixed_count': fixed_count,
            'samples': samples,
        }

        if apply_changes and fixed_count > 0:
            log_action(
                user=None,
                action='score_channel_compat_fix',
                module=OperationLog.MODULE_SCORING,
                level=OperationLog.LEVEL_WARNING,
                target_type='score_record',
                target_id=0,
                target_repr='score_channel_compat_fix',
                extra=summary,
                reason='历史 score_channel 兼容回填',
                is_audit_event=True,
                is_abnormal=False,
                request=None,
            )

        mode_text = 'apply' if apply_changes else 'dry-run'
        self.stdout.write(
            self.style.SUCCESS(
                f'执行完成 mode={mode_text}, total_suspects={total_suspects}, fixed_count={fixed_count}'
            )
        )
