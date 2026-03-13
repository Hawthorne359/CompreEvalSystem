"""
修复历史越界分数：
- ScoreRecord.score
- ArbitrationRecord.score

策略：
- score < 0 => 调整为 0
- score > raw_max_score(indicator) => 调整为上限（若上限存在）
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from audit.models import OperationLog
from audit.services import log_action
from eval.utils import raw_max_score
from scoring.models import ArbitrationRecord, ScoreRecord
from scoring.services import recompute_submission_final_score
from submission.models import StudentSubmission


def _clamp_score(indicator, score):
    """
    计算并返回分值修正结果。
    @returns {(Decimal, str)} (new_score, reason)
    """
    min_score = Decimal('0')
    max_score = raw_max_score(indicator)
    new_score = score
    reason = ''
    if new_score < min_score:
        new_score = min_score
        reason = 'below_min'
    if max_score is not None and new_score > max_score:
        new_score = max_score
        reason = 'above_max'
    return new_score, reason


class Command(BaseCommand):
    help = '修复历史越界分数并记录审计日志'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅扫描并输出统计，不实际写库',
        )
        parser.add_argument(
            '--sample-limit',
            type=int,
            default=20,
            help='审计日志中保留的样本条数',
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get('dry_run'))
        sample_limit = max(int(options.get('sample_limit', 20)), 1)

        fixed_score_records = 0
        fixed_arbitration_records = 0
        affected_submission_ids = set()
        samples = []

        score_qs = ScoreRecord.objects.select_related('indicator', 'submission')
        for rec in score_qs.iterator(chunk_size=500):
            new_score, reason = _clamp_score(rec.indicator, rec.score)
            if new_score == rec.score:
                continue
            if not dry_run:
                old_score = rec.score
                rec.score = new_score
                rec.save(update_fields=['score'])
            else:
                old_score = rec.score
            fixed_score_records += 1
            affected_submission_ids.add(rec.submission_id)
            if len(samples) < sample_limit:
                samples.append({
                    'record_type': 'score_record',
                    'record_id': rec.id,
                    'submission_id': rec.submission_id,
                    'indicator_id': rec.indicator_id,
                    'old_score': str(old_score),
                    'new_score': str(new_score),
                    'reason': reason,
                })

        arb_qs = ArbitrationRecord.objects.select_related('indicator', 'submission')
        for rec in arb_qs.iterator(chunk_size=500):
            new_score, reason = _clamp_score(rec.indicator, rec.score)
            if new_score == rec.score:
                continue
            if not dry_run:
                old_score = rec.score
                rec.score = new_score
                rec.save(update_fields=['score'])
            else:
                old_score = rec.score
            fixed_arbitration_records += 1
            affected_submission_ids.add(rec.submission_id)
            if len(samples) < sample_limit:
                samples.append({
                    'record_type': 'arbitration_record',
                    'record_id': rec.id,
                    'submission_id': rec.submission_id,
                    'indicator_id': rec.indicator_id,
                    'old_score': str(old_score),
                    'new_score': str(new_score),
                    'reason': reason,
                })

        if not dry_run and affected_submission_ids:
            for sid in affected_submission_ids:
                sub = StudentSubmission.objects.filter(pk=sid).first()
                if sub is not None:
                    recompute_submission_final_score(sub)

        summary = {
            'dry_run': dry_run,
            'fixed_score_records': fixed_score_records,
            'fixed_arbitration_records': fixed_arbitration_records,
            'affected_submission_count': len(affected_submission_ids),
            'sample_fixes': samples,
        }

        if not dry_run and (fixed_score_records > 0 or fixed_arbitration_records > 0):
            log_action(
                user=None,
                action='score_outlier_auto_fix',
                module=OperationLog.MODULE_SCORING,
                level=OperationLog.LEVEL_WARNING,
                target_type='score_record',
                target_id=0,
                target_repr='score_outlier_auto_fix',
                extra=summary,
                reason='自动修复历史越界分数',
                is_audit_event=True,
                is_abnormal=True,
                request=None,
            )

        self.stdout.write(self.style.SUCCESS(
            f"扫描完成：fixed_score_records={fixed_score_records}, "
            f"fixed_arbitration_records={fixed_arbitration_records}, "
            f"affected_submission_count={len(affected_submission_ids)}, dry_run={dry_run}"
        ))
