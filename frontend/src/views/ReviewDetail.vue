<template>
  <div class="page-shell">
    <div class="app-breadcrumb">
      <router-link :to="{ name: 'Review' }" class="text-brand-600 hover:underline">{{ isReadonly ? '提交监控' : '审核任务' }}</router-link>
      <span class="text-slate-400">/</span>
      <h2 class="app-breadcrumb-current">{{ isReadonly ? '提交详情' : '审核详情' }}</h2>
    </div>

    <div v-if="loading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="detailError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ detailError }}</div>

    <template v-else-if="detail">
      <div class="app-surface p-4">
        <div class="grid grid-cols-1 gap-3 text-sm md:grid-cols-3">
          <div>
            <div class="text-slate-500">项目</div>
            <div class="font-medium text-slate-800">{{ detail.project_name || '—' }}</div>
          </div>
          <div>
            <div class="text-slate-500">学生</div>
            <div class="flex items-center gap-1.5 font-medium text-slate-800">
              {{ detail.user_student_no || detail.user_name || '—' }}
              <template v-if="detail.user_real_name">（{{ detail.user_real_name }}）</template>
              <span v-if="detail.is_assistant_submission" class="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-700">助理</span>
            </div>
          </div>
          <div>
            <div class="text-slate-500">班级 / 学院</div>
            <div class="font-medium text-slate-800">
              <template v-if="detail.user_class_name || detail.user_department_name">
                {{ detail.user_class_name || '' }}{{ detail.user_class_name && detail.user_department_name ? ' / ' : '' }}{{ detail.user_department_name || '' }}
              </template>
              <template v-else>—</template>
            </div>
          </div>
          <div>
            <div class="text-slate-500">状态</div>
            <StatusBadge :text="statusLabel(detail)" :tone="statusTone(detail)" />
          </div>
          <div>
            <div class="text-slate-500">提交时间</div>
            <div class="text-slate-800">{{ formatDateTime(detail.submitted_at) }}</div>
          </div>
          <div>
            <div class="text-slate-500">最终得分</div>
            <div class="text-slate-800">{{ detail.final_score != null ? detail.final_score : '—' }}</div>
          </div>
          <div>
            <div class="text-slate-500">作答完成度</div>
            <div class="text-slate-800">{{ completedCount }} / {{ reviewQuestions.length }}</div>
          </div>
        </div>
      </div>

      <!-- 助理提交强制审核提示 -->
      <div v-if="detail.is_assistant_submission" class="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
        <strong>注意：</strong>该提交来自{{ roleMeta.nameByLevel(ROLE_LEVEL_ASSISTANT) }}，无论评分是否存在分差，均需{{ roleMeta.nameByLevel(ROLE_LEVEL_COUNSELOR) }}亲自审核确认。
      </div>

      <!-- 降权代劳提示（仅 LV2 降权显示，可通过仲裁通道评分） -->
      <div v-if="canDelegatedScore" class="rounded-lg border border-orange-300 bg-orange-50 px-4 py-2.5 text-sm text-orange-800">
        <strong>降权仲裁模式：</strong>您当前以「{{ auth.user?.current_role?.name }}」身份操作，但您的最高身份等级更高。
        在逐题审核中可提交仲裁评分，仲裁分将直接作为最终成绩并产生完整审计记录。
      </div>

      <!-- 评审老师双评仲裁模式提示 -->
      <div v-if="canCounselorArbitrate" class="rounded-lg border border-orange-300 bg-orange-50 px-4 py-2.5 text-sm text-orange-800">
        <strong>双评仲裁模式：</strong>当前项目开启了双评，常规评分通道仅限{{ roleMeta.nameByLevel(ROLE_LEVEL_ASSISTANT) }}。
        您可在逐题审核中通过仲裁通道直接评分，仲裁分将作为最终成绩。
      </div>

      <!-- 监督视角提示（LV3+只读，包括 LV3 降权用户） -->
      <div v-if="isReadonly" class="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm text-blue-700">
        当前为监督视角（只读）{{ isDelegated ? `，如需仲裁评分请先切换至${roleMeta.nameByLevel(ROLE_LEVEL_COUNSELOR)}角色` : '' }}。如需评分裁定请前往
        <router-link :to="{ name: 'Appeals' }" class="font-medium underline">申诉模块</router-link>。
      </div>

      <div class="app-surface p-4">
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-if="canReleaseToAssistant"
            type="button"
            class="rounded bg-amber-500 px-3 py-1.5 text-sm text-white hover:bg-amber-600 disabled:opacity-50"
            :disabled="releaseLoading"
            @click="doReleaseToAssistant"
          >
            {{ releaseLoading ? '下发中…' : `下发给${assistantLabel}评审` }}
          </button>
          <template v-if="canScore || canDelegatedScore || canCounselorArbitrate || isReadonly">
            <button
              type="button"
              class="rounded px-3 py-1.5 text-sm"
              :class="reviewMode === 'overview' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-700'"
              @click="reviewMode = 'overview'"
            >
              提交总览
            </button>
            <button
              type="button"
              class="rounded px-3 py-1.5 text-sm"
              :class="reviewMode === 'question' ? 'bg-brand-500 text-white shadow-sm' : 'bg-slate-100 text-slate-700'"
              @click="reviewMode = 'question'"
            >
              {{ (canScore || canDelegatedScore || canCounselorArbitrate) ? '逐题审核' : '逐题预览' }}
            </button>
          </template>
        </div>
        <p v-if="releaseMsg" class="mt-2 text-sm" :class="releaseIsError ? 'text-red-600' : 'text-green-600'">{{ releaseMsg }}</p>
      </div>

      <div v-if="reviewMode === 'question' && (canScore || canDelegatedScore || canCounselorArbitrate || isReadonly)" class="app-surface p-4">
        <div class="mb-3 flex items-center justify-between md:hidden">
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50"
            :disabled="currentQuestionIdx <= 0"
            @click="switchQuestion(currentQuestionIdx - 1)"
          >
            上一题
          </button>
          <span class="text-xs text-slate-500">{{ currentQuestionIdx + 1 }} / {{ reviewQuestions.length }}</span>
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50"
            :disabled="currentQuestionIdx >= reviewQuestions.length - 1"
            @click="switchQuestion(currentQuestionIdx + 1)"
          >
            下一题
          </button>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-[260px_1fr]">
          <aside class="hidden rounded-xl border border-slate-200 bg-slate-50/80 p-3 md:block">
            <h3 class="mb-2 text-sm font-medium text-slate-700">题目导航</h3>
            <div class="max-h-[520px] space-y-1 overflow-auto pr-1">
              <button
                v-for="(q, idx) in reviewQuestions"
                :key="q.indicator_id"
                type="button"
                class="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs hover:bg-white"
                :class="idx === currentQuestionIdx ? 'bg-white text-blue-700 ring-1 ring-blue-200' : 'text-slate-700'"
                @click="switchQuestion(idx)"
              >
                <span class="truncate">{{ idx + 1 }}. {{ q.indicator_name }}</span>
                <span :class="q.is_completed ? 'text-green-600' : 'text-amber-600'">{{ q.is_completed ? '已完成' : '未完成' }}</span>
              </button>
            </div>
          </aside>

          <section v-if="currentQuestion" class="min-w-0 space-y-4 overflow-hidden rounded-xl border border-slate-200 bg-white/90 p-4">
            <div>
              <div class="text-xs text-slate-500">{{ currentQuestion.section_name || '未分组模块' }}</div>
              <h3 class="mt-1 text-base font-semibold text-slate-800">{{ currentQuestion.indicator_name }}</h3>
              <div class="mt-1 text-xs text-slate-500">
                <template v-if="currentQuestion.max_score != null">满分：{{ currentQuestion.max_score }}</template>
                <template v-else>无上限</template>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div class="rounded border border-slate-200 bg-slate-50 p-3 text-sm">
                <div class="text-slate-500">学生自评分</div>
                <div class="mt-1 font-medium text-slate-800">{{ currentQuestion.self_score != null ? currentQuestion.self_score : '未填写' }}</div>
              </div>
              <div class="rounded border border-slate-200 bg-slate-50 p-3 text-sm">
                <div class="text-slate-500">本题附件</div>
                <div class="mt-1 font-medium text-slate-800">{{ currentQuestion.evidence_count }}</div>
              </div>
            </div>

            <div class="rounded border border-slate-200 bg-slate-50 p-3">
              <h4 class="text-sm font-medium text-slate-700">
                过程记录
                <span v-if="currentQuestion.require_process_record === false" class="ml-1 text-xs font-normal text-slate-400">（该模块不要求填写）</span>
              </h4>
              <p class="mt-2 whitespace-pre-wrap break-words text-sm text-slate-700">
                {{ currentQuestion.process_record || (currentQuestion.require_process_record === false ? '该模块过程记录为选填，学生未填写' : '学生未填写过程记录') }}
              </p>
            </div>

            <div class="rounded border border-slate-200 bg-slate-50 p-3">
              <h4 class="mb-2 text-sm font-medium text-slate-700">本题佐证材料</h4>
              <AttachmentPreviewList v-if="currentQuestion.evidences?.length" :items="currentQuestion.evidences" />
              <p v-else class="text-xs text-slate-500">本题暂无附件</p>
            </div>

            <template v-if="canScore">
              <div class="space-y-3">
                <div
                  v-if="currentGroupSumCappedInfo"
                  class="rounded border px-3 py-2 text-xs"
                  :class="currentGroupSumCappedInfo.overCap ? 'border-red-200 bg-red-50 text-red-700' : 'border-amber-200 bg-amber-50 text-amber-700'"
                >
                  <span>
                    父项封顶满分 <strong>{{ currentGroupSumCappedInfo.cap }}</strong> 分，
                    其他子项已用 <strong>{{ currentGroupSumCappedInfo.siblingsUsed }}</strong> 分，
                    当前剩余可用 <strong>{{ currentGroupSumCappedInfo.remaining }}</strong> 分
                  </span>
                  <span v-if="currentGroupSumCappedInfo.overCap" class="ml-1 font-medium">
                    （已超出封顶，最终将被截断至 {{ currentGroupSumCappedInfo.cap }} 分）
                  </span>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
                  <div class="sm:w-36">
                    <label class="mb-1 block text-xs text-slate-500">审核分数</label>
                    <input
                      v-model.number="reviewScore"
                      type="number"
                      :min="0"
                      :max="currentGroupSumCappedInfo ? currentGroupSumCappedInfo.remaining : (currentQuestion.max_score != null ? Number(currentQuestion.max_score) : undefined)"
                      step="0.01"
                      placeholder="分数"
                      class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                    />
                  </div>
                  <div class="min-w-0 flex-1">
                    <label class="mb-1 block text-xs text-slate-500">评语（选填）</label>
                    <input
                      v-model="reviewComment"
                      type="text"
                      placeholder="评语"
                      class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                    />
                  </div>
                  <button
                    type="button"
                    class="shrink-0 app-btn app-btn-primary disabled:opacity-50"
                    :disabled="scoreSubmitting"
                    @click="submitCurrentQuestionScore"
                  >
                    {{ scoreSubmitting ? '提交中…' : '提交评分' }}
                  </button>
                </div>
              </div>
              <p v-if="scoreError" class="text-sm text-red-600">{{ scoreError }}</p>
              <p v-if="scoreSuccess" class="text-sm text-green-600">{{ scoreSuccess }}</p>
            </template>
            <template v-else-if="canDelegatedScore">
              <div class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-xs text-orange-700">
                降权仲裁通道：您的评分将以仲裁分直接作为最终成绩，并记录完整审计日志。
              </div>
              <div class="mt-2 flex flex-col gap-2 sm:flex-row sm:items-end">
                <div class="sm:w-36">
                  <label class="mb-1 block text-xs text-slate-500">仲裁分数</label>
                  <input
                    v-model.number="reviewScore"
                    type="number"
                    :min="0"
                    :max="currentQuestion.max_score != null ? Number(currentQuestion.max_score) : undefined"
                    step="0.01"
                    placeholder="分数"
                    class="w-full rounded border border-orange-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div class="min-w-0 flex-1">
                  <label class="mb-1 block text-xs text-slate-500">仲裁评语（选填）</label>
                  <input
                    v-model="reviewComment"
                    type="text"
                    placeholder="评语"
                    class="w-full rounded border border-orange-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <button
                  type="button"
                  class="shrink-0 rounded bg-orange-600 px-4 py-2 text-sm text-white hover:bg-orange-700 disabled:opacity-50"
                  :disabled="scoreSubmitting"
                  @click="submitDelegatedArbitration"
                >
                  {{ scoreSubmitting ? '提交中…' : '提交本题' }}
                </button>
              </div>
              <div class="mt-3 flex items-center gap-3 rounded border border-orange-100 bg-orange-50/50 px-3 py-2">
                <button
                  type="button"
                  class="shrink-0 rounded border border-orange-400 bg-white px-4 py-1.5 text-sm font-medium text-orange-700 hover:bg-orange-50 disabled:opacity-50"
                  :disabled="batchSubmitting || batchFilledCount === 0"
                  @click="saveDraftAndBatchSubmit"
                >
                  {{ batchSubmitting ? '提交中…' : '整套提交仲裁' }}
                </button>
                <span class="text-xs text-orange-600">已填 {{ batchFilledCount }} / {{ reviewQuestions.length }} 题</span>
              </div>
              <p v-if="scoreError" class="text-sm text-red-600">{{ scoreError }}</p>
              <p v-if="scoreSuccess" class="text-sm text-green-600">{{ scoreSuccess }}</p>
              <p v-if="batchError" class="text-sm text-red-600">{{ batchError }}</p>
              <p v-if="batchSuccess" class="text-sm text-green-600">{{ batchSuccess }}</p>
            </template>
            <template v-else-if="canCounselorArbitrate">
              <div class="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-xs text-orange-700">
                评审老师仲裁通道：双评模式下常规评分仅限{{ assistantLabel }}，您的评分将以仲裁分直接作为最终成绩。
              </div>
              <div class="mt-2 flex flex-col gap-2 sm:flex-row sm:items-end">
                <div class="sm:w-36">
                  <label class="mb-1 block text-xs text-slate-500">仲裁分数</label>
                  <input
                    v-model.number="reviewScore"
                    type="number"
                    :min="0"
                    :max="currentQuestion.max_score != null ? Number(currentQuestion.max_score) : undefined"
                    step="0.01"
                    placeholder="分数"
                    class="w-full rounded border border-orange-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <div class="min-w-0 flex-1">
                  <label class="mb-1 block text-xs text-slate-500">仲裁评语（选填）</label>
                  <input
                    v-model="reviewComment"
                    type="text"
                    placeholder="评语"
                    class="w-full rounded border border-orange-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                  />
                </div>
                <button
                  type="button"
                  class="shrink-0 rounded bg-orange-600 px-4 py-2 text-sm text-white hover:bg-orange-700 disabled:opacity-50"
                  :disabled="scoreSubmitting"
                  @click="submitCounselorArbitration"
                >
                  {{ scoreSubmitting ? '提交中…' : '提交本题' }}
                </button>
              </div>
              <div class="mt-3 flex items-center gap-3 rounded border border-orange-100 bg-orange-50/50 px-3 py-2">
                <button
                  type="button"
                  class="shrink-0 rounded border border-orange-400 bg-white px-4 py-1.5 text-sm font-medium text-orange-700 hover:bg-orange-50 disabled:opacity-50"
                  :disabled="batchSubmitting || batchFilledCount === 0"
                  @click="saveDraftAndBatchSubmit"
                >
                  {{ batchSubmitting ? '提交中…' : '整套提交仲裁' }}
                </button>
                <span class="text-xs text-orange-600">已填 {{ batchFilledCount }} / {{ reviewQuestions.length }} 题</span>
              </div>
              <p v-if="scoreError" class="text-sm text-red-600">{{ scoreError }}</p>
              <p v-if="scoreSuccess" class="text-sm text-green-600">{{ scoreSuccess }}</p>
              <p v-if="batchError" class="text-sm text-red-600">{{ batchError }}</p>
              <p v-if="batchSuccess" class="text-sm text-green-600">{{ batchSuccess }}</p>
            </template>
            <div v-if="canRaiseObjection" class="rounded border border-amber-200 bg-amber-50 px-3 py-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <p class="text-xs text-amber-700">当前模块存在拿不准情况时，可发起“异议上报”由上级裁定。</p>
                <button
                  type="button"
                  class="rounded border border-amber-400 bg-white px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-50"
                  @click="openObjectionDialog"
                >
                  异议上报
                </button>
              </div>
              <p v-if="objectionSuccess" class="mt-2 text-xs text-green-600">{{ objectionSuccess }}</p>
              <p v-if="objectionError" class="mt-2 text-xs text-red-600">{{ objectionError }}</p>
            </div>
            <div v-else-if="isReadonly" class="rounded border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
              当前为监督预览模式（只读），不可评分。
            </div>
          </section>
        </div>
      </div>

      <PasswordConfirmDialog
        v-model:visible="showBatchConfirmDialog"
        title="整套仲裁确认"
        message="您即将对该提交的所有已填分题目执行整套仲裁，仲裁分将直接作为最终成绩。此操作不可撤销，请输入密码确认。"
        confirm-text="确认提交仲裁"
        @confirmed="doBatchArbitrate"
      />

      <div v-if="objectionDialogVisible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
        <div class="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
          <h3 class="mb-1 text-base font-semibold text-slate-800">模块异议上报</h3>
          <p class="mb-3 text-xs text-slate-500">模块：{{ currentQuestion?.indicator_name }}</p>
          <textarea
            v-model="objectionReason"
            rows="4"
            class="app-textarea"
            placeholder="请填写为何该模块评分存在异议..."
          />
          <div class="mt-2">
            <label class="mb-1 block text-xs text-slate-500">可选：上传凭证附件（可多选）</label>
            <input type="file" multiple class="text-xs" @change="onObjectionFilesChange" />
            <p v-if="objectionFiles.length" class="mt-1 text-xs text-slate-500">已选择 {{ objectionFiles.length }} 个文件</p>
          </div>
          <p v-if="objectionError" class="mt-2 text-xs text-red-600">{{ objectionError }}</p>
          <div class="mt-4 flex justify-end gap-2">
            <button
              type="button"
              class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
              :disabled="objectionLoading"
              @click="objectionDialogVisible = false"
            >
              取消
            </button>
            <button
              type="button"
              class="rounded bg-amber-600 px-4 py-1.5 text-sm text-white hover:bg-amber-700 disabled:opacity-50"
              :disabled="objectionLoading"
              @click="submitObjection"
            >
              {{ objectionLoading ? '提交中…' : '提交上报' }}
            </button>
          </div>
        </div>
      </div>

      <div class="app-surface p-4">
        <h3 class="mb-3 text-base font-medium text-slate-800">评分记录</h3>
        <div v-if="scoresLoading" class="text-sm text-slate-500">加载评分中…</div>
        <div v-else-if="scores.length" class="app-table-wrap">
          <table class="app-table">
            <thead>
              <tr class="border-b border-slate-200 bg-slate-50">
                <th class="px-3 py-2 text-left font-medium text-slate-700">指标</th>
                <th class="px-3 py-2 text-left font-medium text-slate-700">评审人</th>
                <th v-if="showRoundColumn" class="px-3 py-2 text-left font-medium text-slate-700">轮次</th>
                <th class="px-3 py-2 text-left font-medium text-slate-700">分数</th>
                <th class="px-3 py-2 text-left font-medium text-slate-700">评语</th>
                <th class="px-3 py-2 text-left font-medium text-slate-700">时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in scores" :key="s.id" class="border-b border-slate-100">
                <td class="px-3 py-2 text-slate-800">{{ s.indicator_name }}</td>
                <td class="px-3 py-2 text-slate-800">{{ s.reviewer_name || '—' }}</td>
                <td v-if="showRoundColumn" class="px-3 py-2 text-slate-600">{{ roundLabel(s) }}</td>
                <td class="px-3 py-2 font-medium text-slate-800">{{ s.score }}</td>
                <td class="px-3 py-2 text-slate-600">{{ s.comment || '—' }}</td>
                <td class="px-3 py-2 text-slate-500">{{ formatDateTime(s.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="text-sm text-slate-500">暂无评分记录</p>

        <div v-if="canArbitrate && arbitrationIndicators.length" class="mt-4 rounded border border-amber-200 bg-amber-50 px-4 py-3">
          <p class="text-sm font-medium text-amber-800">以下题目分差超过阈值，可执行仲裁：</p>
          <div class="mt-2 space-y-2">
            <div
              v-for="ai in arbitrationIndicators"
              :key="ai.id"
              class="grid grid-cols-1 items-center gap-2 rounded bg-white p-2 md:grid-cols-[1fr_120px_1fr_auto]"
            >
              <div class="text-sm text-slate-700">{{ ai.name }}（分差 {{ ai.diff }}）</div>
              <input
                v-model.number="arbForm[ai.id].score"
                type="number"
                min="0"
                step="0.01"
                placeholder="仲裁分"
                class="rounded border border-slate-300 px-2 py-1 text-sm focus:border-brand-500 focus:outline-none"
              />
              <input
                v-model="arbForm[ai.id].comment"
                type="text"
                placeholder="仲裁评语（选填）"
                class="rounded border border-slate-300 px-2 py-1 text-sm focus:border-brand-500 focus:outline-none"
              />
              <button
                type="button"
                class="rounded bg-amber-600 px-3 py-1.5 text-sm text-white hover:bg-amber-700 disabled:opacity-50"
                :disabled="arbSubmitting[ai.id]"
                @click="submitArbitration(ai)"
              >
                {{ arbSubmitting[ai.id] ? '提交中…' : '提交仲裁' }}
              </button>
            </div>
          </div>
          <p v-if="arbError" class="mt-2 text-sm text-red-600">{{ arbError }}</p>
          <p v-if="arbSuccess" class="mt-2 text-sm text-green-600">{{ arbSuccess }}</p>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * 审核详情页：
 * - 先看提交总览（基础信息、进度、状态）
 * - 再进入逐题审核（与学生题目化作答对齐）
 * - 支持本题附件在线预览、逐题评分、仲裁打分
 */
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoleMetaStore } from '@/stores/roles'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import {
  getReviewSubmission,
  getReviewScores,
  getReviewQuestions,
  createReviewScore,
  createReviewObjection,
  arbitrateScore,
  batchArbitrateScore,
  releaseAssignments,
} from '@/api/review'
import { getReviewRule } from '@/api/eval'
import { ROLE_LEVEL_ASSISTANT, ROLE_LEVEL_COUNSELOR, ROLE_LEVEL_DIRECTOR } from '@/constants/roles'
import AttachmentPreviewList from '@/components/AttachmentPreviewList.vue'
import PasswordConfirmDialog from '@/components/PasswordConfirmDialog.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'
import { deriveWorkflowSubmissionStatus } from '@/utils/submissionStatus'

const route = useRoute()
const auth = useAuthStore()
const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const assistantLabel = computed(() => roleMeta.nameByLevel(ROLE_LEVEL_ASSISTANT))
const currentLevel = computed(() => auth.user?.current_role?.level ?? -1)

/**
 * @description 用户所有角色中的最高等级，用于检测降权代劳场景。
 * @type {import('vue').ComputedRef<number>}
 */
const maxRoleLevel = computed(() => {
  const roles = (auth.user?.user_roles ?? []).map((ur) => ur.role?.level ?? -1)
  return roles.length ? Math.max(...roles) : -1
})

/**
 * @description 当前是否处于降权代劳状态（最高角色 level 高于当前角色 level）。
 * @type {import('vue').ComputedRef<boolean>}
 */
const isDelegated = computed(() => maxRoleLevel.value > currentLevel.value)

const loading = ref(true)
const detailError = ref('')
const detail = ref(null)
const scores = ref([])
const scoresLoading = ref(false)
const reviewRule = ref(null)
const reviewQuestions = ref([])
const currentQuestionIdx = ref(0)
const reviewMode = ref('overview')

const scoreSubmitting = ref(false)
const scoreError = ref('')
const scoreSuccess = ref('')
const reviewScore = ref(null)
const reviewComment = ref('')

const arbForm = reactive({})
const arbSubmitting = reactive({})
const arbError = ref('')
const arbSuccess = ref('')

const currentQuestion = computed(() => reviewQuestions.value[currentQuestionIdx.value] || null)
const completedCount = computed(() => reviewQuestions.value.filter((q) => q.is_completed).length)

/**
 * 当当前题目的父项为 sum_capped 时，返回该父项的封顶求和剩余可用分信息。
 * 其他情况返回 null。
 */
const currentGroupSumCappedInfo = computed(() => {
  const q = currentQuestion.value
  if (!q || q.parent_agg_formula !== 'sum_capped') return null
  const pid = q.parent_indicator_id
  const cap = Number(q.parent_max_score)
  /** 同父项下其他题目已有的 latest_score 之和（不含当前题本次输入） */
  const siblingsUsed = reviewQuestions.value
    .filter((r) => r.parent_indicator_id === pid && r.indicator_id !== q.indicator_id)
    .reduce((sum, r) => sum + (Number(r.latest_score) || 0), 0)
  const currentUsed = Number(reviewScore.value) || 0
  const totalUsed = siblingsUsed + currentUsed
  return {
    cap,
    siblingsUsed,
    remaining: Math.max(0, cap - siblingsUsed),
    totalUsed,
    overCap: totalUsed > cap,
  }
})

const statusOptions = [
  { value: 'submitted', label: '已提交' },
  { value: 'under_review', label: '审核中' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
  { value: 'draft', label: '草稿' },
  { value: 'appealing', label: '申诉中' },
]

/** @type {import('vue').ComputedRef<boolean>} LV3/LV5 只读监督模式 */
const isReadonly = computed(() => currentLevel.value >= ROLE_LEVEL_DIRECTOR)

/**
 * @description 双评 + 仲裁模式（评审老师不可走常规 assignment 评分通道）
 * @type {import('vue').ComputedRef<boolean>}
 */
const isDualReviewArbitrationOnly = computed(() => {
  const r = reviewRule.value
  if (!r || !r.dual_review_enabled) return false
  const mode = r.counselor_participation_mode || 'arbitration_only'
  return mode === 'arbitration_only'
})

const canScore = computed(() => {
  if (isDelegated.value) return false
  if (isDualReviewArbitrationOnly.value && currentLevel.value === ROLE_LEVEL_COUNSELOR) return false
  return currentLevel.value >= ROLE_LEVEL_ASSISTANT && currentLevel.value <= ROLE_LEVEL_COUNSELOR && ['submitted', 'under_review'].includes(detail.value?.status)
})

/**
 * @description 降权用户在 LV2 时可通过仲裁通道评分
 * @type {import('vue').ComputedRef<boolean>}
 */
const canDelegatedScore = computed(() => {
  return isDelegated.value && currentLevel.value === ROLE_LEVEL_COUNSELOR && ['submitted', 'under_review'].includes(detail.value?.status)
})

/**
 * @description 原生评审老师（非降权）在双评仲裁模式下通过仲裁通道评分
 * @type {import('vue').ComputedRef<boolean>}
 */
const canCounselorArbitrate = computed(() => {
  if (isDelegated.value) return false
  return isDualReviewArbitrationOnly.value
    && currentLevel.value === ROLE_LEVEL_COUNSELOR
    && ['submitted', 'under_review'].includes(detail.value?.status)
})

const canReleaseToAssistant = computed(() => {
  if (isDelegated.value) return false
  return currentLevel.value === ROLE_LEVEL_COUNSELOR && ['submitted', 'under_review'].includes(detail.value?.status)
})
const releaseLoading = ref(false)
const releaseMsg = ref('')
const releaseIsError = ref(false)

/**
 * @description 将当前提交的评审任务下发给学生助理。
 */
async function doReleaseToAssistant() {
  if (!detail.value?.project || !detail.value?.id) return
  releaseLoading.value = true
  releaseMsg.value = ''
  releaseIsError.value = false
  try {
    const res = await releaseAssignments({
      project_id: detail.value.project,
      submission_ids: [detail.value.id],
    })
    releaseMsg.value = `已下发 ${res.created_assistant_tasks ?? 0} 个${assistantLabel.value}评审任务`
    if (res.skipped?.length) {
      releaseMsg.value += `，跳过 ${res.skipped.length} 个（${assistantLabel.value}不足或已分配）`
    }
  } catch (e) {
    releaseIsError.value = true
    const msg = e.response?.data?.detail ?? '下发失败'
    if (msg.includes('尚未生成任务')) {
      releaseMsg.value = '项目尚未生成评审任务分配，请先在「项目配置 → 评审规则」中点击"生成评审任务"'
    } else {
      releaseMsg.value = msg
    }
  } finally {
    releaseLoading.value = false
  }
}

const canArbitrate = computed(() => {
  return currentLevel.value >= ROLE_LEVEL_ASSISTANT && currentLevel.value <= ROLE_LEVEL_COUNSELOR
})

/**
 * @description 助理和辅导员可在审核模块发起模块异议上报。
 * @type {import('vue').ComputedRef<boolean>}
 */
const canRaiseObjection = computed(() => {
  return currentLevel.value >= ROLE_LEVEL_ASSISTANT
    && currentLevel.value <= ROLE_LEVEL_COUNSELOR
    && ['submitted', 'under_review', 'approved'].includes(detail.value?.status)
    && !!currentQuestion.value
})

/**
 * @description 学生助理隐藏轮次，评审老师及以上显示轮次。
 * @type {import('vue').ComputedRef<boolean>}
 */
const showRoundColumn = computed(() => currentLevel.value >= ROLE_LEVEL_COUNSELOR)

const arbitrationIndicators = computed(() => {
  const threshold = reviewRule.value?.score_diff_threshold
  if (threshold == null || !reviewRule.value?.require_arbitration_above_threshold) return []
  const byIndicator = {}
  for (const s of scores.value) {
    if (s.logical_round_type === 3 || s.score_channel === 'arbitration' || s.score_channel === 'import') continue
    if (!byIndicator[s.indicator]) byIndicator[s.indicator] = { id: s.indicator, name: s.indicator_name, scores: [] }
    byIndicator[s.indicator].scores.push(Number(s.score))
  }
  return Object.values(byIndicator)
    .filter((g) => g.scores.length >= 2)
    .map((g) => {
      const diff = Math.abs(Math.max(...g.scores) - Math.min(...g.scores))
      return { id: g.id, name: g.name, diff: diff.toFixed(2) }
    })
    .filter((g) => Number(g.diff) > Number(threshold))
})


/**
 * @description 将当前题目输入框的分数/评语暂存到 batchScores。
 */
function saveDraftToBatch() {
  const q = currentQuestion.value
  if (!q) return
  const id = q.indicator_id
  if (reviewScore.value != null && reviewScore.value !== '') {
    batchScores[id] = { score: reviewScore.value, comment: reviewComment.value || '' }
  }
}

/**
 * 同步当前题目评分输入框。仲裁模式下优先从 batchScores 暂存读取。
 */
function syncCurrentQuestionEditor() {
  const q = currentQuestion.value
  if (!q) return
  const draft = batchScores[q.indicator_id]
  if (draft && draft.score != null) {
    reviewScore.value = draft.score
    reviewComment.value = draft.comment || ''
  } else {
    reviewScore.value = q.latest_score == null ? null : Number(q.latest_score)
    reviewComment.value = q.latest_comment || ''
  }
}

/**
 * 切换题目。切换前自动暂存当前分数到 batchScores。
 * @param {number} idx
 */
function switchQuestion(idx) {
  if (idx < 0 || idx >= reviewQuestions.value.length) return
  if (canCounselorArbitrate.value || canDelegatedScore.value) {
    saveDraftToBatch()
  }
  currentQuestionIdx.value = idx
  scoreError.value = ''
  scoreSuccess.value = ''
  syncCurrentQuestionEditor()
}

function statusLabel(submission) {
  return deriveWorkflowSubmissionStatus(submission).label
}

/**
 * @description 审核详情状态映射到统一徽章语义色。
 * @param {Object} submission
 * @returns {string}
 */
function statusTone(submission) {
  return deriveWorkflowSubmissionStatus(submission).tone
}

/**
 * @description 渲染评分记录轮次，优先使用后端返回的逻辑轮次。
 * @param {Record<string, any>} scoreRecord
 * @returns {string}
 */
function roundLabel(scoreRecord) {
  if (scoreRecord?.logical_round_label) return scoreRecord.logical_round_label
  const rt = Number(scoreRecord?.round_type)
  if (rt === 1) return '一评'
  if (rt === 2) return '二评'
  if (rt === 3) return '仲裁'
  if (scoreRecord?.score_channel === 'import') return '导入'
  return Number.isInteger(rt) && rt > 0 ? `第${rt}轮` : '未知轮次'
}

/**
 * @description 统一校验单题分值范围（前端快速失败；最终以后端校验为准）。
 * @param {number|string|null} rawScore
 * @param {string} indicatorName
 * @param {number|string|null|undefined} maxScore
 * @param {boolean} [isRecordOnly=false]
 * @returns {string}
 */
function validateScoreInput(rawScore, indicatorName, maxScore, isRecordOnly = false) {
  if (isRecordOnly) return ''
  if (rawScore == null || rawScore === '') return `请输入「${indicatorName}」的分数`
  const scoreNum = Number(rawScore)
  if (Number.isNaN(scoreNum)) return `「${indicatorName}」分数格式无效，请输入数字`
  if (scoreNum < 0) return `「${indicatorName}」分数越界，不能小于 0`
  if (maxScore !== null && maxScore !== undefined && maxScore !== '') {
    const maxNum = Number(maxScore)
    if (!Number.isNaN(maxNum) && scoreNum > maxNum) {
      return `「${indicatorName}」分数越界，不能大于满分 ${maxNum}`
    }
  }
  return ''
}

async function submitCurrentQuestionScore() {
  if (!detail.value?.id || !currentQuestion.value) return
  const localError = validateScoreInput(
    reviewScore.value,
    currentQuestion.value.indicator_name || '当前题目',
    currentQuestion.value.max_score,
    !!currentQuestion.value.is_record_only,
  )
  if (localError) {
    scoreError.value = localError
    return
  }
  scoreSubmitting.value = true
  scoreError.value = ''
  scoreSuccess.value = ''
  try {
    await createReviewScore(detail.value.id, {
      indicator_id: currentQuestion.value.indicator_id,
      score: reviewScore.value,
      comment: reviewComment.value || '',
    })
    scoreSuccess.value = '本题评分提交成功'
    await Promise.all([loadScores(), loadQuestions(), refreshDetail()])
    syncCurrentQuestionEditor()
  } catch (e) {
    scoreError.value = e.response?.data?.detail ?? '评分提交失败'
  } finally {
    scoreSubmitting.value = false
  }
}

/**
 * @description 降权用户在逐题审核中提交仲裁评分（走仲裁API）。
 */
async function submitDelegatedArbitration() {
  if (!detail.value?.id || !currentQuestion.value) return
  const localError = validateScoreInput(
    reviewScore.value,
    currentQuestion.value.indicator_name || '当前题目',
    currentQuestion.value.max_score,
    !!currentQuestion.value.is_record_only,
  )
  if (localError) {
    scoreError.value = localError
    return
  }
  scoreSubmitting.value = true
  scoreError.value = ''
  scoreSuccess.value = ''
  try {
    await arbitrateScore(detail.value.id, {
      indicator_id: currentQuestion.value.indicator_id,
      score: reviewScore.value,
      comment: reviewComment.value || '',
    })
    delete batchScores[currentQuestion.value.indicator_id]
    scoreSuccess.value = '本题仲裁评分提交成功'
    await Promise.all([loadScores(), loadQuestions(), refreshDetail()])
    syncCurrentQuestionEditor()
  } catch (e) {
    scoreError.value = e.response?.data?.detail ?? '仲裁评分提交失败'
  } finally {
    scoreSubmitting.value = false
  }
}

/**
 * @description 评审老师在双评仲裁模式下通过仲裁接口评分。
 */
async function submitCounselorArbitration() {
  if (!detail.value?.id || !currentQuestion.value) return
  const localError = validateScoreInput(
    reviewScore.value,
    currentQuestion.value.indicator_name || '当前题目',
    currentQuestion.value.max_score,
    !!currentQuestion.value.is_record_only,
  )
  if (localError) {
    scoreError.value = localError
    return
  }
  scoreSubmitting.value = true
  scoreError.value = ''
  scoreSuccess.value = ''
  try {
    await arbitrateScore(detail.value.id, {
      indicator_id: currentQuestion.value.indicator_id,
      score: reviewScore.value,
      comment: reviewComment.value || '',
    })
    delete batchScores[currentQuestion.value.indicator_id]
    scoreSuccess.value = '本题仲裁评分提交成功'
    await Promise.all([loadScores(), loadQuestions(), refreshDetail()])
    syncCurrentQuestionEditor()
  } catch (e) {
    scoreError.value = e.response?.data?.detail ?? '仲裁评分提交失败'
  } finally {
    scoreSubmitting.value = false
  }
}

function initArbForm() {
  for (const ai of arbitrationIndicators.value) {
    if (!arbForm[ai.id]) {
      arbForm[ai.id] = { score: null, comment: '' }
      arbSubmitting[ai.id] = false
    }
  }
}

/**
 * 提交仲裁打分。
 * @param {{id:number,name:string}} ai
 */
async function submitArbitration(ai) {
  const form = arbForm[ai.id]
  const question = reviewQuestions.value.find((q) => q.indicator_id === ai.id)
  const localError = validateScoreInput(form.score, ai.name, question?.max_score, !!question?.is_record_only)
  if (localError) {
    arbError.value = localError
    return
  }
  arbError.value = ''
  arbSuccess.value = ''
  arbSubmitting[ai.id] = true
  try {
    await arbitrateScore(detail.value.id, {
      indicator_id: ai.id,
      score: form.score,
      comment: form.comment || '',
    })
    arbSuccess.value = `「${ai.name}」仲裁分提交成功`
    form.score = null
    form.comment = ''
    await Promise.all([loadScores(), loadQuestions(), refreshDetail()])
  } catch (e) {
    arbError.value = e.response?.data?.detail ?? '仲裁失败'
  } finally {
    arbSubmitting[ai.id] = false
  }
}

// ── 整套仲裁 ──
const batchScores = reactive({})
const batchSubmitting = ref(false)
const batchError = ref('')
const batchSuccess = ref('')
const showBatchConfirmDialog = ref(false)
const objectionDialogVisible = ref(false)
const objectionReason = ref('')
const objectionFiles = ref([])
const objectionLoading = ref(false)
const objectionError = ref('')
const objectionSuccess = ref('')

const batchFilledCount = computed(() => {
  return reviewQuestions.value.filter((q) => {
    const entry = batchScores[q.indicator_id]
    return entry && entry.score != null && entry.score !== ''
  }).length
})

/**
 * @description 暂存当前题目分数后弹出密码确认对话框，准备整套提交。
 */
function saveDraftAndBatchSubmit() {
  saveDraftToBatch()
  if (batchFilledCount.value === 0) {
    batchError.value = '请至少为一题填写仲裁分数（逐题填写后会自动暂存）'
    return
  }
  batchError.value = ''
  batchSuccess.value = ''
  showBatchConfirmDialog.value = true
}

/**
 * @description 密码验证通过后批量提交仲裁。
 * @param {{ confirmToken: string, reason: string }} payload
 */
async function doBatchArbitrate({ confirmToken }) {
  saveDraftToBatch()
  const scoresToSubmit = reviewQuestions.value
    .filter((q) => {
      const entry = batchScores[q.indicator_id]
      return entry && entry.score != null && entry.score !== ''
    })
    .map((q) => ({
      indicator_id: q.indicator_id,
      score: batchScores[q.indicator_id].score,
      comment: batchScores[q.indicator_id].comment || '',
    }))
  if (!scoresToSubmit.length) {
    batchError.value = '请至少为一题填写仲裁分数'
    return
  }
  for (const q of reviewQuestions.value) {
    const entry = batchScores[q.indicator_id]
    if (!entry || entry.score == null || entry.score === '') continue
    const localError = validateScoreInput(entry.score, q.indicator_name || '当前题目', q.max_score, !!q.is_record_only)
    if (localError) {
      batchError.value = localError
      return
    }
  }
  batchSubmitting.value = true
  batchError.value = ''
  batchSuccess.value = ''
  try {
    const result = await batchArbitrateScore(detail.value.id, {
      confirm_token: confirmToken,
      scores: scoresToSubmit,
    })
    batchSuccess.value = result.detail || '整套仲裁提交成功'
    for (const key of Object.keys(batchScores)) delete batchScores[key]
    await Promise.all([loadScores(), loadQuestions(), refreshDetail()])
    syncCurrentQuestionEditor()
  } catch (e) {
    batchError.value = e.response?.data?.detail ?? '整套仲裁提交失败'
  } finally {
    batchSubmitting.value = false
  }
}

/**
 * 打开发起异议弹窗并重置表单。
 */
function openObjectionDialog() {
  objectionDialogVisible.value = true
  objectionReason.value = ''
  objectionFiles.value = []
  objectionError.value = ''
  objectionSuccess.value = ''
}

/**
 * 选择异议附件。
 * @param {Event} e
 */
function onObjectionFilesChange(e) {
  objectionFiles.value = Array.from(e.target?.files || [])
}

/**
 * 提交当前模块异议上报。
 */
async function submitObjection() {
  if (!detail.value?.id || !currentQuestion.value) return
  if (!objectionReason.value.trim()) {
    objectionError.value = '请填写异议理由'
    return
  }
  objectionLoading.value = true
  objectionError.value = ''
  objectionSuccess.value = ''
  try {
    await createReviewObjection(
      detail.value.id,
      currentQuestion.value.indicator_id,
      objectionReason.value.trim(),
      objectionFiles.value,
    )
    objectionSuccess.value = '异议已上报'
    objectionDialogVisible.value = false
  } catch (e) {
    objectionError.value = e.response?.data?.detail ?? '异议上报失败'
  } finally {
    objectionLoading.value = false
  }
}

async function loadScores() {
  const id = route.params.id
  if (!id) return
  scoresLoading.value = true
  try {
    scores.value = await getReviewScores(id)
  } catch {
    scores.value = []
  } finally {
    scoresLoading.value = false
  }
}

async function loadQuestions() {
  const id = route.params.id
  if (!id) return
  try {
    reviewQuestions.value = await getReviewQuestions(id)
    if (currentQuestionIdx.value >= reviewQuestions.value.length) currentQuestionIdx.value = 0
    syncCurrentQuestionEditor()
  } catch {
    reviewQuestions.value = []
  }
}

async function loadReviewRuleData() {
  if (!detail.value?.project) return
  try {
    reviewRule.value = await getReviewRule(detail.value.project)
  } catch {
    reviewRule.value = null
  }
}

async function refreshDetail() {
  try {
    detail.value = await getReviewSubmission(route.params.id)
  } catch {
    /* 静默刷新失败 */
  }
}

async function loadDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  detailError.value = ''
  try {
    detail.value = await getReviewSubmission(id)
    await Promise.all([loadScores(), loadQuestions(), loadReviewRuleData()])
  } catch (e) {
    detailError.value = e.response?.data?.detail ?? '加载失败'
    detail.value = null
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, loadDetail)
watch(arbitrationIndicators, () => initArbForm(), { immediate: true })

onMounted(() => {
  loadDetail()
})

useRealtimeRefresh(['submission', 'score'], refreshDetail)
</script>
