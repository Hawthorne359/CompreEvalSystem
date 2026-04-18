"""
测评周期、项目、指标与规则模型。
"""
from django.db import models


class EvalSeason(models.Model):
    """测评周期（学年/学期）。"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('ongoing', '进行中'),
        ('closed', '已结束'),
    ]
    name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eval_season'
        ordering = ['-academic_year', '-semester']

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class EvalProject(models.Model):
    """某次测评项目。"""
    season = models.ForeignKey(
        EvalSeason,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='draft')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='项目开始时间（学生提交开放）')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='项目结束时间（学生提交截止）')
    review_end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='成绩评定截止时间',
        help_text='教师评分截止时间，可晚于项目结束时间，但不得晚于测评周期结束时间',
    )
    allow_late_submit = models.BooleanField(default=False)
    late_submit_deadline = models.DateTimeField(null=True, blank=True)
    import_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Excel 批量导入列映射配置，留空使用系统默认（第0列学号，第1列指标名，第2列分数）。'
            '示例：{"student_col": 0, "indicator_col": 1, "score_col": 2, '
            '"student_field": "student_no", "comment": "批量导入", "module_import_modes": {"A1":"import"}}'
        ),
    )
    report_visibility_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            '学生报表可见策略，由直属评审老师配置。'
            '字段：ranking_enabled, ranking_scope(class/major), show_peer_identity, '
            'show_total_score, show_indicator_breakdown, show_my_rank_in_class, show_my_rank_in_major'
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eval_project'
        ordering = ['season', 'id']

    def __str__(self):
        return self.name


class EvalIndicator(models.Model):
    """测评指标/维度。支持两级父子结构：一级维度（parent=null）和二级子项（parent=一级维度）。"""

    AGG_FORMULA_CHOICES = [
        ('sum', '求和'),
        ('weighted_sum', '加权求和'),
        ('average', '平均'),
        ('sum_capped', '封顶求和'),
    ]
    SCORE_SOURCE_CHOICES = [
        ('reviewer', '评审打分'),
        ('import', '统一导入'),
        ('self', '学生自评'),
        ('children', '由子项汇总'),
    ]

    project = models.ForeignKey(
        EvalProject,
        on_delete=models.CASCADE,
        related_name='indicators',
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        help_text='父级指标；为空表示一级维度',
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text='评分细则说明（可选）')
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text='仅一级指标使用，用于映射总分权重规则（如 F1/F2/德育/智育）',
    )
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100,
        null=True,
        blank=True,
        help_text='满分/上限；仅记录性指标（is_record_only=True）可留空表示无上限限制',
    )
    weight = models.FloatField(
        default=1.0,
        help_text='二级子项：在父级加权求和中的权重；一级指标：占总分比例（在权重规则中配置）',
    )
    agg_formula = models.CharField(
        max_length=20,
        choices=AGG_FORMULA_CHOICES,
        default='sum',
        help_text='仅一级指标有意义：子项聚合方式（求和 / 加权求和 / 封顶求和）',
    )
    score_source = models.CharField(
        max_length=20,
        choices=SCORE_SOURCE_CHOICES,
        default='reviewer',
        help_text='叶节点（无子项）时有意义：评分来源；含子项时建议选 children（由子项聚合得来）',
    )
    is_record_only = models.BooleanField(
        default=False,
        help_text='仅记录存档，不纳入父级分数聚合（如门次、绩点等辅助字段）',
    )
    require_process_record = models.BooleanField(
        default=True,
        help_text='学生自评时是否强制要求填写过程记录；设为 False 则该模块只需填分数即可完成',
    )
    record_only_requires_review = models.BooleanField(
        default=False,
        help_text='仅记录模块是否仍需推送给评审人复核（不参与总分计算，仅决定是否进入评审链路）',
    )
    grade_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            '年级差异化评分规则，仅叶子指标有意义。格式：'
            '{"rules":[{"min_year":1,"max_year":2,"max_score":40,"coefficient":1.0},...]}。'
            'min_year/max_year 为在读年级数（1=大一），max_score 为 null 时沿用默认满分，'
            'coefficient 为分数乘数（如 0.4 表示取原始分的 40%）。'
        ),
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eval_indicator'
        ordering = ['project', 'order', 'id']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ScoreWeightRule(models.Model):
    """总分构成规则（A*X%+B*Y%+...）。"""
    project = models.OneToOneField(
        EvalProject,
        on_delete=models.CASCADE,
        related_name='weight_rule',
    )
    formula_type = models.CharField(max_length=50, default='weighted_sum')
    formula_config = models.JSONField(default=dict, help_text='如 {"A":0.3,"B":0.3,"C":0.2,"D":0.2}')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eval_score_weight_rule'

    def __str__(self):
        return f"WeightRule({self.project.name})"


class ReviewRule(models.Model):
    """双评与仲裁规则。"""
    REVIEW_SCOPE_MODE_CHOICES = [
        ('same_class', '仅本班'),
        ('same_counselor_classes', '同辅导员名下跨班'),
        ('same_major', '同专业'),
    ]
    FINAL_SCORE_RULE_CHOICES = [
        ('average', '平均分'),
        ('max', '最高分'),
        ('first', '第一评'),
    ]
    COUNSELOR_PARTICIPATION_MODE_CHOICES = [
        ('arbitration_only', '仅超阈值仲裁介入'),
        ('always_confirm', '每份提交最终确认'),
    ]
    SINGLE_REVIEW_MODE_CHOICES = [
        ('assistant_single', '学生助理单评'),
        ('counselor_single', '辅导员单评'),
    ]
    project = models.OneToOneField(
        EvalProject,
        on_delete=models.CASCADE,
        related_name='review_rule',
    )
    dual_review_enabled = models.BooleanField(default=True)
    review_scope_mode = models.CharField(
        max_length=50,
        choices=REVIEW_SCOPE_MODE_CHOICES,
        default='same_class',
        help_text='双评分配范围策略',
    )
    cross_class_shuffle_enabled = models.BooleanField(
        default=False,
        help_text='跨班分配时是否打散随机分配',
    )
    allowed_assistant_count_per_submission = models.PositiveSmallIntegerField(
        default=2,
        help_text='每份提交分配的学生助理人数（至少2名）',
    )
    counselor_participation_mode = models.CharField(
        max_length=30,
        choices=COUNSELOR_PARTICIPATION_MODE_CHOICES,
        default='arbitration_only',
        help_text='辅导员介入模式：仅仲裁介入 / 每份最终确认',
    )
    single_review_mode = models.CharField(
        max_length=30,
        choices=SINGLE_REVIEW_MODE_CHOICES,
        default='assistant_single',
        help_text='单评执行人模式：学生助理单评 / 辅导员单评',
    )
    score_diff_threshold = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='分差超过此值触发仲裁',
    )
    overall_score_diff_threshold = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='总分差超过此值触发仲裁（为空时回落到通用分差阈值）',
    )
    module_diff_thresholds = models.JSONField(
        default=dict,
        blank=True,
        help_text='按模块配置分差阈值，如 {"A1": 5, "B1": 8}',
    )
    final_score_rule = models.CharField(
        max_length=20,
        choices=FINAL_SCORE_RULE_CHOICES,
        default='average',
    )
    allow_view_other_scores = models.BooleanField(default=False)
    require_arbitration_above_threshold = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eval_review_rule'

    def __str__(self):
        return f"ReviewRule({self.project.name})"


class EvalProjectConfigTemplate(models.Model):
    """测评项目配置模板。"""
    VISIBILITY_CHOICES = [
        ('private', '仅自己可见'),
        ('global', '全局可见'),
    ]
    name = models.CharField(max_length=120)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='eval_project_config_templates',
    )
    include_sections = models.JSONField(default=list, blank=True, help_text='保存片段：basic/indicator/weight/review')
    payload = models.JSONField(default=dict, blank=True, help_text='模板快照内容')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eval_project_config_template'
        ordering = ['-updated_at', '-id']

    def __str__(self):
        return f"ConfigTemplate({self.name})"
