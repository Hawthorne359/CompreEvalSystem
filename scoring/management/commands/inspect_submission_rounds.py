"""
只读排查命令：按学号输出提交、任务分配、评分轮次覆盖情况。
"""
from django.core.management.base import BaseCommand, CommandError

from scoring.models import ReviewAssignment, ScoreRecord
from submission.models import StudentSubmission
from users.models import User


class Command(BaseCommand):
    help = '按学号只读排查提交-任务-轮次-评分人链路'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-no',
            required=True,
            help='学生学号，例如 202284014041',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='输出最近提交数，默认 10',
        )

    def handle(self, *args, **options):
        student_no = str(options['student_no']).strip()
        limit = max(int(options.get('limit', 10)), 1)
        user = User.objects.filter(student_no=student_no).first()
        if user is None:
            raise CommandError(f'未找到学号为 {student_no} 的用户')

        self.stdout.write(self.style.SUCCESS(
            f'用户: id={user.id}, username={user.username}, name={user.name or ""}, student_no={student_no}'
        ))

        submissions = list(
            StudentSubmission.objects.filter(user=user)
            .select_related('project')
            .order_by('-id')[:limit]
        )
        if not submissions:
            self.stdout.write('该用户暂无提交记录')
            return

        for sub in submissions:
            self.stdout.write('-' * 80)
            self.stdout.write(
                f'SUBMISSION id={sub.id}, project={sub.project_id}:{sub.project.name}, '
                f'status={sub.status}, final_score={sub.final_score}'
            )

            assignments = (
                ReviewAssignment.objects.filter(submission=sub)
                .select_related('reviewer')
                .order_by('id')
            )
            self.stdout.write('  assignments:')
            for a in assignments:
                reviewer_name = a.reviewer.username if a.reviewer else 'None'
                self.stdout.write(
                    f'    - id={a.id}, reviewer={a.reviewer_id}:{reviewer_name}, '
                    f'role_type={a.role_type}, round_type={a.round_type}, status={a.status}'
                )

            records = (
                ScoreRecord.objects.filter(submission=sub)
                .select_related('reviewer')
                .order_by('round_type', 'reviewer_id', 'indicator_id')
            )
            self.stdout.write('  score_records:')
            for r in records:
                reviewer_name = r.reviewer.username if r.reviewer else 'None'
                self.stdout.write(
                    f'    - id={r.id}, reviewer={r.reviewer_id}:{reviewer_name}, '
                    f'round_type={r.round_type}, indicator={r.indicator_id}, score={r.score}'
                )
