<template>
  <div class="page-shell" @click="clearHighlight">
    <nav class="app-breadcrumb">
      <router-link :to="{ name: 'Seasons' }" class="text-brand-600 hover:underline">测评周期</router-link>
      <span>/</span>
      <router-link
        v-if="project?.season"
        :to="{ name: 'SeasonProjects', params: { seasonId: project.season } }"
        class="text-brand-600 hover:underline"
      >
        {{ seasonName }}
      </router-link>
      <template v-else><span class="text-slate-500">…</span></template>
      <span>/</span>
      <span class="app-breadcrumb-current">{{ project?.name || '加载中…' }}</span>
    </nav>

    <div v-if="projectLoadError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ projectLoadError }}
    </div>

    <template v-else>
      <section class="app-surface mb-4 p-4">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label class="block text-sm text-slate-700">
              模板名称（保存时使用）
              <input
                v-model="templateDraft.name"
                type="text"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
                placeholder="如：2024-综合测评标准模板"
              />
            </label>
            <label class="block text-sm text-slate-700">
              可见范围
              <select
                v-model="templateDraft.visibility"
                class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              >
                <option value="private">仅自己可见</option>
                <option value="global">全局可见</option>
              </select>
            </label>
            <label class="block text-sm text-slate-700 sm:col-span-2">
              套用模板
              <select
                v-model="selectedTemplateId"
                class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              >
                <option value="">请选择模板</option>
                <option v-for="tpl in templateList" :key="tpl.id" :value="String(tpl.id)">
                  {{ tpl.name }}（{{ tpl.created_by_name || '未知创建人' }}）
                </option>
              </select>
            </label>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="app-btn app-btn-secondary disabled:opacity-50"
              :disabled="templateSaving"
              @click="saveTemplateFromCurrent"
            >
              {{ templateSaving ? '保存中…' : '保存为模板' }}
            </button>
            <button
              type="button"
              class="rounded border border-emerald-300 px-3 py-2 text-sm text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
              :disabled="templateApplying || !selectedTemplateId"
              @click="applySelectedTemplate"
            >
              {{ templateApplying ? '应用中…' : '套用模板' }}
            </button>
            <button
              type="button"
              class="rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              :disabled="templateLoading"
              @click="loadTemplateList"
            >
              {{ templateLoading ? '刷新中…' : '刷新模板' }}
            </button>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-600">
          <label class="inline-flex items-center gap-1">
            <input v-model="templateDraft.sections.basic" type="checkbox" class="rounded border-slate-300" />
            基本信息
          </label>
          <label class="inline-flex items-center gap-1">
            <input v-model="templateDraft.sections.indicator" type="checkbox" class="rounded border-slate-300" />
            指标结构
          </label>
          <label class="inline-flex items-center gap-1">
            <input v-model="templateDraft.sections.weight" type="checkbox" class="rounded border-slate-300" />
            权重规则
          </label>
          <label class="inline-flex items-center gap-1">
            <input v-model="templateDraft.sections.review" type="checkbox" class="rounded border-slate-300" />
            评审规则
          </label>
          <button
            type="button"
            class="rounded border border-slate-200 px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-50"
            @click="selectAllTemplateSections"
          >
            一键全选
          </button>
        </div>
        <p v-if="templateError" class="mt-2 text-sm text-red-600">{{ templateError }}</p>
      </section>

      <div class="border-b border-slate-200">
        <nav class="flex gap-1 overflow-x-auto whitespace-nowrap">
          <button
            v-for="t in tabs"
            :key="t.id"
            type="button"
            class="border-b-2 px-3 py-2 text-sm font-medium transition-colors"
            :class="activeTab === t.id ? 'border-brand-500 text-brand-600' : 'border-transparent text-slate-600 hover:text-slate-900'"
            @click="activeTab = t.id"
          >
            {{ t.label }}
          </button>
        </nav>
      </div>

      <!-- Tab: 基本信息 -->
      <section v-show="activeTab === 'basic'" class="app-surface p-4 md:p-6">
        <h4 class="mb-4 text-base font-medium text-slate-800">项目基本信息</h4>
        <!-- 周期时间参考 -->
        <p v-if="project?.season_start_time || project?.season_end_time" class="mb-3 text-xs text-slate-500">
          所属测评周期时间：{{ formatDateTime(project.season_start_time) }} — {{ formatDateTime(project.season_end_time) }}
        </p>
        <form class="max-w-xl space-y-3" @submit.prevent="saveBasic">
          <label class="block text-sm text-slate-700">
            项目名称
            <input
              v-model="basicForm.name"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <label class="block text-sm text-slate-700">
            描述
            <textarea
              v-model="basicForm.description"
              rows="3"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <div class="block text-sm text-slate-700">
            状态
            <select
              v-model="basicForm.status"
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="draft">草稿</option>
              <option value="ongoing" :disabled="!canBeOngoing">进行中{{ canBeOngoing ? '' : '（不可用）' }}</option>
              <option value="closed">已结束</option>
            </select>
            <p v-if="!canBeOngoing" class="mt-1 text-xs text-amber-600">
              当前项目时间窗口已结束且迟交截止时间已过，"进行中"不可选。
              如需继续，请修改下方的项目时间，或勾选允许迟交并设置未来的截止时间。
            </p>
          </div>

          <!-- 项目时间配置 -->
          <div class="rounded border border-slate-100 bg-slate-50 p-3 space-y-3">
            <p class="text-xs font-medium text-slate-600">项目时间（须在测评周期时间范围内）</p>
            <label class="block text-sm text-slate-700">
              开始时间（学生提交开放，选填）
              <input
                v-model="basicForm.start_time"
                type="datetime-local"
                :min="seasonMinDatetime"
                :max="basicForm.end_time || seasonMaxDatetime"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
            </label>
            <label class="block text-sm text-slate-700">
              结束时间（学生提交截止，选填）
              <input
                v-model="basicForm.end_time"
                type="datetime-local"
                :min="basicForm.start_time || seasonMinDatetime"
                :max="seasonMaxDatetime"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
            </label>
            <label class="block text-sm text-slate-700">
              成绩评定截止时间（选填，可晚于项目结束时间）
              <input
                v-model="basicForm.review_end_time"
                type="datetime-local"
                :min="basicForm.end_time || basicForm.start_time || seasonMinDatetime"
                :max="seasonMaxDatetime"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
              <span class="text-xs text-slate-400">教师可在此时间前完成评分，设置后超时将无法打分</span>
            </label>
          </div>

          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="basicForm.allow_late_submit" type="checkbox" class="rounded border-slate-300" />
            允许迟交
          </label>
          <label v-if="basicForm.allow_late_submit" class="block text-sm text-slate-700">
            迟交截止时间（必须晚于项目结束时间且不晚于成绩评定截止时间）
            <input
              v-model="basicForm.late_submit_deadline"
              type="datetime-local"
              :min="basicForm.end_time || undefined"
              :max="basicForm.review_end_time || seasonMaxDatetime"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <p v-if="basicError" class="text-sm text-red-600">{{ basicError }}</p>
          <button
            type="submit"
            class="app-btn app-btn-primary app-btn-sm disabled:opacity-50"
            :disabled="basicSaving"
          >
            {{ basicSaving ? '保存中…' : '保存' }}
          </button>
        </form>
      </section>

      <!-- Tab: 指标列表（树状结构） -->
      <section v-show="activeTab === 'indicators'" class="app-surface p-4 md:p-6">
        <div class="mb-3 flex items-center justify-between">
          <h4 class="text-base font-medium text-slate-800">指标结构</h4>
          <button
            type="button"
            class="app-btn app-btn-primary app-btn-sm"
            @click="openTopIndicatorCreate"
          >
            + 添加一级指标
          </button>
        </div>
        <p class="mb-4 text-xs text-slate-500">
          一级指标对应测评维度（如德育 F1、智育 F2），其「类别」用于对应总分权重。二级子项是一级指标下的具体评分项。
        </p>
        <div v-if="indicatorLoading" class="py-8 text-center text-slate-500">加载中…</div>
        <div v-else-if="indicatorTree.length === 0" class="rounded border border-slate-100 bg-slate-50 py-8 text-center text-sm text-slate-500">
          暂无指标，请点击「添加一级指标」开始配置
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="root in indicatorTree"
            :key="root.id"
            class="rounded border border-slate-200 bg-white"
          >
            <IndicatorTreeNode
              :node="root"
              :depth="1"
              :max-depth="5"
              :highlight-id="lastHighlightIndicatorId"
              @add-child="openChildCreate"
              @edit="openEdit"
              @delete="confirmDeleteIndicator"
            />
          </div>
        </div>
      </section>

      <!-- Tab: 总分权重规则（维度来自指标列表的「类别」） -->
      <section v-show="activeTab === 'weight'" class="app-surface p-4 md:p-6">
        <h4 class="mb-2 text-base font-medium text-slate-800">总分权重规则</h4>
        <p class="mb-4 text-xs text-slate-500">权重维度与「指标列表」中各指标的「类别」一一对应，建议权重之和为 1。</p>
        <div v-if="weightLoading" class="py-4 text-slate-500">加载中…</div>
        <div v-else-if="weightKeys.length === 0" class="rounded border border-slate-200 bg-slate-50 py-6 px-4 text-sm text-slate-600">
          请先在「指标列表」中添加指标，指标的「类别」（如 A、B、C、F 或 思想道德、学业成绩 等）将作为总分权重的维度。
        </div>
        <form v-else class="max-w-md space-y-3" @submit.prevent="saveWeight">
          <div
            v-for="key in weightKeys"
            :key="key"
            class="flex items-center gap-3"
          >
            <label class="w-20 text-sm font-medium text-slate-700">{{ key }}</label>
            <input
              v-model.number="weightForm[key]"
              type="number"
              step="0.01"
              min="0"
              max="1"
              class="w-24 rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </div>
          <p v-if="weightError" class="text-sm text-red-600">{{ weightError }}</p>
          <button
            type="submit"
            class="app-btn app-btn-primary app-btn-sm disabled:opacity-50"
            :disabled="weightSaving"
          >
            {{ weightSaving ? '保存中…' : '保存' }}
          </button>
        </form>
      </section>

      <!-- Tab: 评审规则 -->
      <section v-show="activeTab === 'review'" class="app-surface p-4 md:p-6">
        <h4 class="mb-2 text-base font-medium text-slate-800">双评与仲裁规则</h4>
        <p class="mb-4 text-xs text-slate-500">双评开启时，以助理独立评分为主；{{ counselorLabel }}是否参与常规评分由“介入模式”决定。分差超过阈值可触发仲裁。</p>
        <div v-if="reviewLoading" class="py-4 text-slate-500">加载中…</div>
        <form v-else class="max-w-xl space-y-4" @submit.prevent="saveReview">
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="reviewForm.dual_review_enabled" type="checkbox" class="rounded border-slate-300" />
            启用双评/多评（助理独立评分）
            <span
              class="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500"
              title="默认每份提交分配2名助理独立评分；可将人数调高到3~5。{{ counselorLabel }}默认仅在超阈值时仲裁介入。"
            >i</span>
          </label>
          <label class="block text-sm text-slate-700">
            双评范围策略
            <select
              v-model="reviewForm.review_scope_mode"
              class="mt-1 rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              :disabled="!reviewForm.dual_review_enabled"
            >
              <option value="same_class">仅本班</option>
              <option value="same_counselor_classes">同{{ counselorLabel }}名下跨班互评</option>
              <option value="same_major">同专业混评</option>
            </select>
            <span
              class="mt-1 inline-flex items-center gap-1 text-xs text-slate-500"
              title="示例：同专业混评=计算机专业内A/B/C班互评；同{{ counselorLabel }}跨班=仅该{{ counselorLabel }}负责班级互评；仅本班=班内助理互评。"
            >
              <span class="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500">i</span>
              范围决定“助理候选池”从哪里取人
            </span>
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input
              v-model="reviewForm.cross_class_shuffle_enabled"
              type="checkbox"
              class="rounded border-slate-300"
              :disabled="!reviewForm.dual_review_enabled || !['same_counselor_classes', 'same_major'].includes(reviewForm.review_scope_mode)"
            />
            跨班评审打散分配（同{{ counselorLabel }}跨班 / 同专业混评模式生效）
            <span
              class="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500"
              title="打散=在候选池内随机化分配，避免总是固定助理命中同一批提交，提升均衡性。"
            >i</span>
          </label>
          <label class="block text-sm text-slate-700">
            {{ counselorLabel }}介入模式
            <select
              v-model="reviewForm.counselor_participation_mode"
              class="mt-1 rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              :disabled="!reviewForm.dual_review_enabled"
            >
              <option value="arbitration_only">仅超阈值仲裁介入（默认）</option>
              <option value="always_confirm">每份提交最终确认</option>
            </select>
            <span
              class="mt-1 inline-flex items-center gap-1 text-xs text-slate-500"
              title="仅仲裁介入：助理先评，分差超阈值再由{{ counselorLabel }}仲裁；每份最终确认：{{ counselorLabel }}会额外收到确认任务。"
            >
              <span class="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500">i</span>
              建议默认“仅超阈值仲裁介入”以降低常规工作量
            </span>
          </label>
          <label class="block text-sm text-slate-700">
            单评执行人（仅在关闭双评时生效）
            <select
              v-model="reviewForm.single_review_mode"
              class="mt-1 rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              :disabled="reviewForm.dual_review_enabled"
            >
              <option value="assistant_single">{{ assistantLabel }}单评（异常可上报{{ counselorLabel }}）</option>
              <option value="counselor_single">{{ counselorLabel }}单评</option>
            </select>
            <span
              class="mt-1 inline-flex items-center gap-1 text-xs text-slate-500"
              title="关闭双评后，系统按此配置为每份提交仅分配1名执行人。重新开启双评时，此值会保留，便于后续切换回单评。"
            >
              <span class="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500">i</span>
              双评关闭时启用；双评开启时自动置灰保留
            </span>
          </label>
          <label class="block text-sm text-slate-700">
            每份提交分配助理人数
            <input
              v-model.number="reviewForm.allowed_assistant_count_per_submission"
              type="number"
              min="2"
              max="5"
              class="mt-1 w-32 rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              :disabled="!reviewForm.dual_review_enabled"
            />
          </label>
          <label class="block text-sm text-slate-700">
            通用分差阈值（模块未单独设置时生效）
            <input
              v-model="reviewForm.score_diff_threshold"
              type="number"
              step="0.01"
              min="0"
              class="mt-1 w-32 rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如 5"
            />
          </label>
          <label class="block text-sm text-slate-700">
            总分差阈值（可选）
            <input
              v-model="reviewForm.overall_score_diff_threshold"
              type="number"
              step="0.01"
              min="0"
              class="mt-1 w-40 rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如 10"
            />
            <span class="mt-0.5 block text-xs text-slate-400">用于比较同一提交在不同评审人总分上的差值</span>
          </label>
          <div class="rounded border border-slate-200 bg-slate-50 p-3">
            <p class="text-sm font-medium text-slate-700">模块分差阈值（按一级指标类别）</p>
            <p class="mt-1 text-xs text-slate-500">未配置的模块会自动回落到“通用分差阈值”。</p>
            <div v-if="topLevelCategories.length" class="mt-2 grid gap-2 sm:grid-cols-2">
              <label v-for="cat in topLevelCategories" :key="cat" class="block text-xs text-slate-700">
                {{ cat }}
                <input
                  v-model="reviewForm.module_diff_thresholds[cat]"
                  type="number"
                  step="0.01"
                  min="0"
                  class="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                  :placeholder="String(reviewForm.score_diff_threshold || '')"
                />
              </label>
            </div>
            <p v-else class="mt-2 text-xs text-slate-400">暂无一级指标类别，先在“指标结构”中配置 category。</p>
          </div>
          <label class="block text-sm text-slate-700">
            最终分取法
            <select
              v-model="reviewForm.final_score_rule"
              class="mt-1 rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="average">平均分</option>
              <option value="max">最高分</option>
              <option value="first">第一评</option>
            </select>
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="reviewForm.allow_view_other_scores" type="checkbox" class="rounded border-slate-300" />
            允许查看他人评分
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="reviewForm.require_arbitration_above_threshold" type="checkbox" class="rounded border-slate-300" />
            分差超过阈值时必须仲裁
          </label>
          <p v-if="reviewError" class="text-sm text-red-600">{{ reviewError }}</p>
          <div class="flex items-center gap-2">
            <button
              type="submit"
              class="app-btn app-btn-primary app-btn-sm disabled:opacity-50"
              :disabled="reviewSaving"
            >
              {{ reviewSaving ? '保存中…' : '保存规则' }}
            </button>
            <button
              type="button"
              class="app-btn app-btn-ghost app-btn-sm disabled:opacity-50"
              :disabled="assignGenerating"
              @click="generateAssignmentsNow"
            >
              {{ assignGenerating ? '生成中…' : generateTaskButtonLabel }}
            </button>
            <span v-if="assignSummary" class="text-xs text-slate-500">
              已分配 {{ assignSummary.total }} 条任务
            </span>
            <span class="text-xs text-slate-400">
              仅为尚未分配的提交创建评审任务，已有任务不受影响
            </span>
          </div>
        </form>
      </section>
    </template>

    <!-- 一级指标 新建/编辑 弹窗 -->
    <div
      v-if="topModalOpen"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
    >
      <div class="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-lg border border-slate-200 bg-white p-6 shadow">
        <h4 class="text-base font-medium text-slate-800">{{ editingTopIndicator ? '编辑一级指标' : '添加一级指标' }}</h4>
        <p class="mt-1 text-xs text-slate-500">一级指标对应测评大维度，如德育、智育、体育等。</p>
        <form class="mt-4 space-y-3" @submit.prevent="submitTopIndicator">
          <label class="block text-sm text-slate-700">
            名称 <span class="text-red-500">*</span>
            <input
              v-model="topForm.name"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：德育评分"
            />
          </label>
          <label class="block text-sm text-slate-700">
            类别标识 <span class="text-red-500">*</span>
            <input
              v-model="topForm.category"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：F1（用于总分权重规则中的键）"
            />
            <span class="mt-0.5 block text-xs text-slate-400">将在「总分权重规则」中作为该维度的标识</span>
          </label>
          <label class="block text-sm text-slate-700">
            子项聚合方式
            <select
              v-model="topForm.agg_formula"
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="sum">求和（F = A1 + A2 + A3 …）</option>
              <option value="weighted_sum">加权求和（F = A1×w1 + A2×w2 …）</option>
              <option value="average">平均（F = (A1 + A2 + A3) / n）</option>
              <option value="sum_capped">封顶求和（子项合计不超过本级满分）</option>
            </select>
          </label>
          <div class="block text-sm text-slate-700">
            <span v-if="topForm.is_record_only" class="text-slate-500">上限（可选）</span>
            <span v-else>满分</span>
            <template v-if="!topForm.is_record_only && topForm.agg_formula === 'sum' && editingTopIndicator && topFormChildrenSum > 0">
              <!-- 编辑模式 + sum + 有子项：显示只读自动汇总值 -->
              <div class="mt-1 flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500">
                <span class="font-medium text-slate-700">{{ topFormChildrenSum }}</span>
                <span class="text-xs text-slate-400">（求和模式由子项自动汇总，当前子项满分之和）</span>
              </div>
            </template>
            <template v-else-if="!topForm.grade_rules_enabled">
              <!-- 未启用年级规则时：可手动输入（记录性可留空） -->
              <input
                v-model.number="topForm.max_score"
                type="number"
                step="0.01"
                min="0"
                :placeholder="topForm.is_record_only ? '不填表示无上限' : ''"
                class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              />
              <span v-if="topForm.is_record_only" class="mt-0.5 block text-xs text-slate-400">
                记录性指标可不设上限；如需限制最大录入值可在此填写。
              </span>
              <span v-else-if="topForm.agg_formula === 'sum'" class="mt-0.5 block text-xs text-slate-400">
                求和模式下添加子项后将自动更新为子项满分之和
              </span>
            </template>
            <template v-else>
              <!-- 启用年级规则时：满分由规则行各自定义，此处不显示输入框 -->
              <p class="mt-1 text-xs text-slate-400">满分由下方各年级规则行分别指定。</p>
            </template>
          </div>
          <label class="block text-sm text-slate-700">
            说明（可选）
            <textarea
              v-model="topForm.description"
              rows="2"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="评分细则或备注"
            />
          </label>
          <label class="block text-sm text-slate-700">
            评分来源
            <!-- 有子项时：锁定为「由子项汇总」，不允许选其他来源 -->
            <template v-if="editingTopIndicator && editingTopIndicator.children?.length">
              <div class="mt-1 flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
                <span class="font-medium text-teal-600">由子项汇总</span>
                <span class="text-xs text-slate-400">（该指标含子项，得分由子项聚合计算得来）</span>
              </div>
            </template>
            <!-- 无子项时：允许选具体来源 -->
            <template v-else>
              <select
                v-model="topForm.score_source"
                class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              >
                <option value="self">学生自评（学生填报后由评审确认）</option>
                <option value="import">统一导入（由{{ adminLabel }} Excel 批量导入）</option>
              </select>
              <span class="mt-0.5 block text-xs text-slate-400">添加子项后将自动变为「由子项汇总」</span>
            </template>
          </label>
          <label class="flex cursor-pointer items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <input
              v-model="topForm.require_process_record"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-brand-500"
            />
            <span>学生端该模块要求填写过程记录</span>
          </label>
          <p class="text-xs text-slate-400">关闭后，学生在该模块可仅填写分数，过程记录可留空。</p>

          <!-- 记录性标记 -->
          <label class="flex cursor-pointer items-center gap-2 rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-slate-700">
            <input
              v-model="topForm.is_record_only"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-orange-500"
            />
            <span>仅记录存档（不参与分数聚合）</span>
          </label>
          <p v-if="topForm.is_record_only" class="text-xs text-orange-600">已设为记录性指标：其分值不会被父级聚合计算，仅用于存档和表格展示。</p>
          <label
            v-if="topForm.is_record_only && topForm.score_source === 'self'"
            class="flex cursor-pointer items-center gap-2 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-slate-700"
          >
            <input
              v-model="topForm.record_only_requires_review"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-amber-500"
            />
            <span>仅记录模块仍推送评阅人复核</span>
          </label>
          <p v-if="topForm.is_record_only && topForm.score_source === 'self'" class="text-xs text-slate-400">
            关闭后，该模块不进入评审流程；导出仅保留记录值（不展示确认分）。
          </p>

          <!-- 年级差异规则（单层级模式下有意义） -->
          <div class="rounded border border-slate-200 bg-slate-50 p-3 space-y-2">
            <label class="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-700">
              <input
                v-model="topForm.grade_rules_enabled"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 accent-brand-500"
              />
              按年级配置满分和系数
            </label>
            <p class="text-xs text-slate-400">仅在该一级指标不含子项（单层级模式）时有效；不同在读年级独立指定满分和得分系数。</p>

            <div v-if="topForm.grade_rules_enabled" class="space-y-2">
              <!-- 列标题 -->
              <div class="flex items-center gap-2 px-2 text-xs font-medium text-slate-500">
                <span class="w-24 shrink-0">在读年级段</span>
                <span class="w-24 shrink-0">满分（必填）</span>
                <span class="w-20 shrink-0">系数</span>
                <span class="w-24 shrink-0">规则名（可选）</span>
              </div>
              <!-- 规则行 -->
              <div
                v-for="(rule, idx) in topForm.grade_rules_list"
                :key="idx"
                class="flex items-center gap-2 rounded border border-slate-200 bg-white px-2 py-1.5"
              >
                <div class="flex shrink-0 items-center gap-1 w-24">
                  <input
                    v-model.number="rule.min_year"
                    type="number"
                    min="1"
                    max="9"
                    required
                    placeholder="1"
                    class="w-10 rounded border border-slate-300 px-1 py-1 text-center text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                  />
                  <span class="shrink-0 text-xs text-slate-400">~</span>
                  <input
                    v-model.number="rule.max_year"
                    type="number"
                    min="1"
                    max="9"
                    required
                    placeholder="5"
                    class="w-10 rounded border border-slate-300 px-1 py-1 text-center text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                  />
                </div>
                <input
                  v-model.number="rule.max_score"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  placeholder="如 40"
                  class="w-24 shrink-0 rounded border border-slate-300 px-2 py-1 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <input
                  v-model.number="rule.coefficient"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="1"
                  class="w-20 shrink-0 rounded border border-slate-300 px-2 py-1 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <input
                  v-model="rule.label"
                  type="text"
                  placeholder="如 大一大二"
                  class="w-24 shrink-0 rounded border border-slate-300 px-2 py-1 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <button
                  type="button"
                  class="ml-auto shrink-0 text-slate-400 hover:text-red-500 text-sm leading-none"
                  @click="removeTopGradeRule(idx)"
                >✕</button>
              </div>
              <button
                type="button"
                class="rounded border border-dashed border-slate-300 px-3 py-1 text-xs text-slate-500 hover:border-brand-400 hover:text-brand-600"
                @click="addTopGradeRule"
              >+ 添加规则行</button>
              <p class="text-xs text-slate-400">系数 1.0 = 不变，0.4 = 原始分 × 40%；未覆盖的年级按最后一条规则兜底。</p>
            </div>
          </div>

          <label class="block text-sm text-slate-700">
            排序
            <input
              v-model.number="topForm.order"
              type="number"
              min="0"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <p v-if="topModalError" class="text-sm text-red-600">{{ topModalError }}</p>
          <div class="mt-4 flex justify-end gap-2">
            <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="closeTopModal">取消</button>
            <button type="submit" class="app-btn app-btn-primary app-btn-sm disabled:opacity-50" :disabled="topSubmitting">
              {{ topSubmitting ? '提交中…' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 二级子项 新建/编辑 弹窗 -->
    <div
      v-if="childModalOpen"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
    >
      <div class="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-lg border border-slate-200 bg-white p-6 shadow">
        <h4 class="text-base font-medium text-slate-800">
          {{ editingChildIndicator ? '编辑子项' : '添加子项' }}
          <span class="ml-1 text-sm font-normal text-slate-500">— {{ childParent?.name }}</span>
        </h4>
        <form class="mt-4 space-y-3" @submit.prevent="submitChildIndicator">

          <!-- 名称 -->
          <label class="block text-sm text-slate-700">
            名称 <span class="text-red-500">*</span>
            <input
              v-model="childForm.name"
              type="text"
              required
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：思想品德表现"
            />
          </label>

          <!-- 满分配置区块：固定满分 OR 年级差异规则（互斥） -->
          <div class="rounded border border-slate-200 bg-slate-50 p-3 space-y-2">
            <!-- 父项为封顶求和时：只读灰显满分 + 说明 -->
            <div v-if="childParent?.agg_formula === 'sum_capped'">
              <div class="flex items-center gap-2">
                <span class="text-sm text-slate-700">满分</span>
                <input
                  :value="childParent?.max_score"
                  type="number"
                  disabled
                  class="w-32 rounded border border-slate-200 bg-slate-100 px-3 py-1.5 text-sm text-slate-400 cursor-not-allowed"
                />
              </div>
              <p class="mt-1 text-xs text-slate-400">
                父项满分 {{ childParent?.max_score }} 分，子项不单独设置满分。所有子项得分之和自动封顶至父项满分。
              </p>
            </div>

            <!-- 非封顶求和：正常满分配置 -->
            <template v-else>
              <!-- 模式切换开关（记录性子项无需年级规则，隐藏此选项） -->
              <label v-if="!childForm.is_record_only" class="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-700">
                <input
                  v-model="childForm.grade_rules_enabled"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300 accent-brand-500"
                />
                按年级配置满分和系数
              </label>

              <!-- 模式 A：固定满分（或记录性可选上限） -->
              <div v-if="!childForm.grade_rules_enabled">
                <label class="block text-sm text-slate-700">
                  <span v-if="childForm.is_record_only" class="text-slate-500">上限（可选）</span>
                  <span v-else>满分</span>
                  <input
                    v-model.number="childForm.max_score"
                    type="number"
                    step="0.01"
                    min="0"
                    :placeholder="childForm.is_record_only ? '不填表示无上限（如门次、绩点等）' : ''"
                    class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
                  />
                  <span v-if="childForm.is_record_only" class="mt-0.5 block text-xs text-slate-400">
                    记录性字段可不设上限。如需限制最大录入值（如绩点最高 5.0），在此填写；否则留空。
                  </span>
                </label>
              </div>

              <!-- 模式 B：年级差异规则表格 -->
              <div v-else class="space-y-2">
                <p class="text-xs text-slate-400">不同在读年级（大一=1）独立指定满分和得分系数，如体育 C1 大一大二 40 分、大三起 20 分。</p>
              <!-- 列标题（与规则行对齐） -->
              <div class="flex items-center gap-2 px-2 text-xs font-medium text-slate-500">
                <span class="w-24 shrink-0">在读年级段</span>
                <span class="w-24 shrink-0">满分（必填）</span>
                <span class="w-20 shrink-0">系数</span>
                <span class="w-24 shrink-0">规则名（可选）</span>
              </div>
              <!-- 规则行 -->
              <div
                v-for="(rule, idx) in childForm.grade_rules_list"
                :key="idx"
                class="flex items-center gap-2 rounded border border-slate-200 bg-white px-2 py-1.5"
              >
                <!-- 年级范围：min ~ max，shrink-0 防止被压缩 -->
                <div class="flex shrink-0 items-center gap-1 w-24">
                  <input
                    v-model.number="rule.min_year"
                    type="number"
                    min="1"
                    max="9"
                    required
                    placeholder="1"
                    class="w-10 rounded border border-slate-300 px-1 py-1 text-center text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                  />
                  <span class="shrink-0 text-xs text-slate-400">~</span>
                  <input
                    v-model.number="rule.max_year"
                    type="number"
                    min="1"
                    max="9"
                    required
                    placeholder="5"
                    class="w-10 rounded border border-slate-300 px-1 py-1 text-center text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                  />
                </div>
                <!-- 满分（必填） -->
                <input
                  v-model.number="rule.max_score"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  placeholder="如 40"
                  class="w-24 shrink-0 rounded border border-slate-300 px-2 py-1 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <!-- 系数 -->
                <input
                  v-model.number="rule.coefficient"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="1"
                  class="w-20 shrink-0 rounded border border-slate-300 px-2 py-1 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <!-- 规则名 -->
                <input
                  v-model="rule.label"
                  type="text"
                  placeholder="如 大一大二"
                  class="w-24 shrink-0 rounded border border-slate-300 px-2 py-1 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
                />
                <!-- 删除，ml-auto 推到最右 -->
                <button
                  type="button"
                  class="ml-auto shrink-0 text-slate-400 hover:text-red-500 text-sm leading-none"
                  @click="removeGradeRule(idx)"
                >✕</button>
              </div>

              <button
                type="button"
                class="rounded border border-dashed border-slate-300 px-3 py-1 text-xs text-slate-500 hover:border-brand-400 hover:text-brand-600"
                @click="addGradeRule"
              >+ 添加规则行</button>
              <p class="text-xs text-slate-400">系数 1.0 = 不变，0.4 = 原始分 × 40%；未覆盖的年级按最后一条规则兜底。</p>
            </div>
            </template>
          </div>

          <!-- 权重（仅加权求和时显示） -->
          <label v-if="childParent?.agg_formula === 'weighted_sum'" class="block text-sm text-slate-700">
            权重（在父级加权求和中的比例）
            <input
              v-model.number="childForm.weight"
              type="number"
              step="0.01"
              min="0"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="如：0.85"
            />
            <span class="mt-0.5 block text-xs text-slate-400">所有子项权重之和建议为 1</span>
          </label>

          <!-- 子项聚合方式（当该子项本身还有下级子项时使用） -->
          <label class="block text-sm text-slate-700">
            子项聚合方式
            <select
              v-model="childForm.agg_formula"
              class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="sum">求和（F = A1 + A2 + A3 …）</option>
              <option value="weighted_sum">加权求和（F = A1×w1 + A2×w2 …）</option>
              <option value="average">平均（F = (A1 + A2 + A3) / n）</option>
              <option value="sum_capped">封顶求和（子项合计不超过本级满分）</option>
            </select>
            <span class="mt-0.5 block text-xs text-slate-400">若此子项将来需要再添加下级子项，在此选择聚合方式；否则忽略。</span>
          </label>

          <!-- 评分来源（作为叶节点时有效） -->
          <label class="block text-sm text-slate-700">
            评分来源
            <!-- 有下级子项时：锁定为「由子项汇总」 -->
            <template v-if="editingChildIndicator && editingChildIndicator.children?.length">
              <div class="mt-1 flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
                <span class="font-medium text-teal-600">由子项汇总</span>
                <span class="text-xs text-slate-400">（该子项含下级子项，得分由子项聚合计算得来）</span>
              </div>
            </template>
            <!-- 无子项时：正常选择 -->
            <template v-else>
              <select
                v-model="childForm.score_source"
                class="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              >
                <option value="self">学生自评（学生填报后由评审确认）</option>
                <option value="import">统一导入（由{{ adminLabel }} Excel 批量导入）</option>
              </select>
              <span class="mt-0.5 block text-xs text-slate-400">添加下级子项后将自动变为「由子项汇总」</span>
            </template>
          </label>
          <label class="flex cursor-pointer items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <input
              v-model="childForm.require_process_record"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-brand-500"
            />
            <span>学生端该模块要求填写过程记录</span>
          </label>
          <p class="text-xs text-slate-400">关闭后，学生在该模块可仅填写分数，过程记录可留空。</p>

          <!-- 记录性标记 -->
          <label class="flex cursor-pointer items-center gap-2 rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-slate-700">
            <input
              v-model="childForm.is_record_only"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-orange-500"
            />
            <span>仅记录存档（不参与父级分数聚合）</span>
          </label>
          <p v-if="childForm.is_record_only" class="text-xs text-orange-600">已设为记录性子项：此项分值不会被父级聚合计算，仅用于存档和表格展示（如课门次、绩点等辅助字段）。</p>
          <label
            v-if="childForm.is_record_only && childForm.score_source === 'self'"
            class="flex cursor-pointer items-center gap-2 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-slate-700"
          >
            <input
              v-model="childForm.record_only_requires_review"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 accent-amber-500"
            />
            <span>仅记录模块仍推送评阅人复核</span>
          </label>
          <p v-if="childForm.is_record_only && childForm.score_source === 'self'" class="text-xs text-slate-400">
            关闭后，该模块不进入评审流程；导出仅保留记录值（不展示确认分）。
          </p>

          <!-- 说明 -->
          <label class="block text-sm text-slate-700">
            说明（可选）
            <textarea
              v-model="childForm.description"
              rows="2"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="评分细则或备注"
            />
          </label>

          <!-- 排序 -->
          <label class="block text-sm text-slate-700">
            排序
            <input
              v-model.number="childForm.order"
              type="number"
              min="0"
              class="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
            />
          </label>

          <p v-if="childModalError" class="text-sm text-red-600">{{ childModalError }}</p>
          <div class="mt-4 flex justify-end gap-2">
            <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="closeChildModal">取消</button>
            <button type="submit" class="app-btn app-btn-primary app-btn-sm disabled:opacity-50" :disabled="childSubmitting">
              {{ childSubmitting ? '提交中…' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 删除指标确认 -->
    <div
      v-if="deleteTarget"
      class="fixed inset-0 z-20 flex items-center justify-center bg-black/30"
    >
      <div class="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow">
        <p class="text-slate-800">
          确定删除{{ deleteTargetIsParent ? '一级指标' : '指标' }}「{{ deleteTarget.name }}」吗？
        </p>
        <p class="mt-1 text-xs text-orange-600">
          注意：删除该指标将同时删除其所有子项及相关评分记录。
        </p>
        <p v-if="deleteError" class="mt-2 text-xs text-red-600">{{ deleteError }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50" @click="deleteTarget = null; deleteError = ''">取消</button>
          <button type="button" class="rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700" :disabled="deleteLoading" @click="doDeleteIndicator">
            {{ deleteLoading ? '删除中…' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 项目配置页：基本信息、指标结构（两级树）、总分权重规则、评审规则。
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import IndicatorTreeNode from './IndicatorTreeNode.vue'
import {
  getProject,
  updateProject,
  getIndicatorTree,
  createIndicator,
  updateIndicator,
  deleteIndicator,
  getWeightRule,
  updateWeightRule,
  getReviewRule,
  updateReviewRule,
  getSeasons,
  getProjectConfigTemplates,
  saveProjectConfigTemplate,
  applyProjectConfigTemplate,
} from '@/api/eval'
import { generateReviewAssignments, getProjectAssignmentSummary } from '@/api/review'
import { formatDateTime } from '@/utils/format'
import { useRoleMetaStore } from '@/stores/roles'

const route = useRoute()
const roleMeta = useRoleMetaStore()
const router = useRouter()
const projectId = computed(() => Number(route.params.projectId))

const counselorLabel = computed(() => roleMeta.nameByLevel(2))
const assistantLabel = computed(() => roleMeta.nameByLevel(1))
const adminLabel = computed(() => roleMeta.nameByLevel(5))

const project = ref(null)
const projectLoadError = ref('')
const seasonList = ref([])
const seasonName = computed(() => {
  if (!project.value?.season) return ''
  const s = seasonList.value.find((x) => x.id === project.value.season)
  return s?.name ?? ''
})
const templateList = ref([])
const templateLoading = ref(false)
const templateSaving = ref(false)
const templateApplying = ref(false)
const templateError = ref('')
const selectedTemplateId = ref('')
const templateDraft = ref({
  name: '',
  visibility: 'private',
  sections: {
    basic: true,
    indicator: true,
    weight: true,
    review: true,
  },
})

function pickedTemplateSections() {
  const sec = templateDraft.value.sections
  return Object.keys(sec).filter((k) => !!sec[k])
}

function selectAllTemplateSections() {
  templateDraft.value.sections = {
    basic: true,
    indicator: true,
    weight: true,
    review: true,
  }
}

async function loadTemplateList() {
  templateLoading.value = true
  templateError.value = ''
  try {
    templateList.value = await getProjectConfigTemplates()
  } catch (e) {
    templateError.value = e.response?.data?.detail ?? '加载模板列表失败'
    templateList.value = []
  } finally {
    templateLoading.value = false
  }
}

async function saveTemplateFromCurrent() {
  templateError.value = ''
  const name = (templateDraft.value.name || '').trim()
  if (!name) {
    templateError.value = '请先输入模板名称'
    return
  }
  const sections = pickedTemplateSections()
  if (!sections.length) {
    templateError.value = '请至少选择一个模板片段'
    return
  }
  templateSaving.value = true
  try {
    await saveProjectConfigTemplate(projectId.value, {
      name,
      visibility: templateDraft.value.visibility || 'private',
      sections,
    })
    await loadTemplateList()
  } catch (e) {
    templateError.value = e.response?.data?.detail ?? '保存模板失败'
  } finally {
    templateSaving.value = false
  }
}

async function applySelectedTemplate() {
  templateError.value = ''
  if (!selectedTemplateId.value) {
    templateError.value = '请先选择模板'
    return
  }
  const sections = pickedTemplateSections()
  if (!sections.length) {
    templateError.value = '请至少选择一个应用片段'
    return
  }
  const ok = window.confirm('套用模板会覆盖你选中的配置片段，是否继续？')
  if (!ok) return
  templateApplying.value = true
  try {
    await applyProjectConfigTemplate(projectId.value, Number(selectedTemplateId.value), { sections })
    await loadProject()
    await loadIndicators()
    await loadWeightRule()
    await loadReviewRule()
  } catch (e) {
    templateError.value = e.response?.data?.detail ?? '套用模板失败'
  } finally {
    templateApplying.value = false
  }
}

const tabs = [
  { id: 'basic', label: '基本信息' },
  { id: 'indicators', label: '指标结构' },
  { id: 'weight', label: '总分权重规则' },
  { id: 'review', label: '评审规则' },
]
const activeTab = ref('basic')

// ─── 基本信息 ────────────────────────────────────────────────────────────────
const basicForm = ref({
  name: '',
  description: '',
  status: 'draft',
  start_time: '',
  end_time: '',
  review_end_time: '',
  allow_late_submit: false,
  late_submit_deadline: '',
})
const basicSaving = ref(false)
const basicError = ref('')

/** Season datetime-local min/max for input constraints */
const seasonMinDatetime = computed(() => toLocalDatetimeStr(project.value?.season_start_time))
const seasonMaxDatetime = computed(() => toLocalDatetimeStr(project.value?.season_end_time))

function toLocalDatetimeStr(isoStr) {
  if (!isoStr) return undefined
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return undefined
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/**
 * 判断当前项目是否满足"进行中"状态的条件：
 * - 条件 A：当前时间在项目自有时间窗口内（无则回退测评周期时间）
 * - 条件 B：表单中"允许迟交"开启且迟交截止时间仍在未来
 * 两个条件满足其一即可选"进行中"；否则该选项置灰。
 */
const canBeOngoing = computed(() => {
  const now = new Date()
  const form = basicForm.value

  // 条件 A1：项目自有时间窗口
  const pStart = form.start_time ? new Date(form.start_time) : null
  const pEnd = form.end_time ? new Date(form.end_time) : null
  const projectWindowValid = pStart && pEnd && pStart <= now && now <= pEnd

  // 条件 A2：回退到测评周期时间（项目无自有时间时）
  let seasonValid = false
  if (!pStart && !pEnd) {
    const sStart = project.value?.season_start_time ? new Date(project.value.season_start_time) : null
    const sEnd = project.value?.season_end_time ? new Date(project.value.season_end_time) : null
    seasonValid = !!(sStart && sEnd && sStart <= now && now <= sEnd)
  }

  // 条件 B：迟交窗口仍开放
  const lateDeadline = form.late_submit_deadline ? new Date(form.late_submit_deadline) : null
  const lateValid = !!(form.allow_late_submit && lateDeadline && lateDeadline > now)

  return !!(projectWindowValid || seasonValid || lateValid)
})

// ─── 指标树 ───────────────────────────────────────────────────────────────────
const indicatorTree = ref([])        // 根指标数组，每项含递归 children
const indicatorLoading = ref(false)

// 一级指标弹窗
const topModalOpen = ref(false)
const editingTopIndicator = ref(null)
const topForm = ref({ name: '', category: '', agg_formula: 'sum', max_score: 100, score_source: 'reviewer', description: '', order: 0, grade_rules_enabled: false, grade_rules_list: [], is_record_only: false, require_process_record: true, record_only_requires_review: false })
const topModalError = ref('')
const topSubmitting = ref(false)

// 二级子项弹窗
const childModalOpen = ref(false)
const editingChildIndicator = ref(null)
const childParent = ref(null)         // 当前操作的父级指标
const childForm = ref({ name: '', max_score: 100, weight: 1, agg_formula: 'sum', score_source: 'self', description: '', order: 0, grade_rules_enabled: false, grade_rules_list: [], is_record_only: false, require_process_record: true, record_only_requires_review: false })
const childModalError = ref('')
const childSubmitting = ref(false)

// 删除确认
const deleteTarget = ref(null)
const deleteTargetIsParent = ref(false)
const deleteLoading = ref(false)
const deleteError = ref('')

/** 最近编辑的指标 ID，用于树节点高亮，点击页面任意处清除 */
const lastHighlightIndicatorId = ref(null)

// ─── 权重规则 ─────────────────────────────────────────────────────────────────
const weightKeys = ref([])
const weightForm = ref({})
const weightLoading = ref(false)
const weightSaving = ref(false)
const weightError = ref('')

// ─── 评审规则 ─────────────────────────────────────────────────────────────────
const reviewForm = ref({
  dual_review_enabled: true,
  review_scope_mode: 'same_class',
  cross_class_shuffle_enabled: false,
  allowed_assistant_count_per_submission: 2,
  counselor_participation_mode: 'arbitration_only',
  single_review_mode: 'assistant_single',
  score_diff_threshold: null,
  overall_score_diff_threshold: null,
  module_diff_thresholds: {},
  final_score_rule: 'average',
  allow_view_other_scores: false,
  require_arbitration_above_threshold: true,
})
const reviewLoading = ref(false)
const reviewSaving = ref(false)
const reviewError = ref('')
const assignGenerating = ref(false)
const assignSummary = ref(null)
const topLevelCategories = computed(() => {
  const rows = indicatorTree.value || []
  return [...new Set(rows.map((i) => String(i.category || '').trim()).filter(Boolean))]
})
const generateTaskButtonLabel = computed(() => (
  reviewForm.value.dual_review_enabled ? '补充分配任务' : '补充分配任务'
))

/**
 * 一级指标弹窗中求和模式下的子项满分之和。
 * 新建时无子项返回 0；编辑时从 indicatorTree 中找到对应父级的子项计算。
 */
const topFormChildrenSum = computed(() => {
  if (!editingTopIndicator.value) return 0
  const parent = indicatorTree.value.find((p) => p.id === editingTopIndicator.value.id)
  if (!parent || !parent.children?.length) return 0
  return parent.children.reduce((sum, c) => sum + Number(c.max_score ?? 0), 0)
})

function _extractError(e) {
  if (!e.response) return '网络错误'
  const d = e.response.data
  if (typeof d === 'string') return d
  if (d?.detail) return d.detail
  if (d?.parent) return Array.isArray(d.parent) ? d.parent[0] : d.parent
  if (d?.name) return Array.isArray(d.name) ? d.name[0] : d.name
  return '保存失败'
}

// ─── 加载 ─────────────────────────────────────────────────────────────────────
async function loadProject() {
  if (!projectId.value) return
  projectLoadError.value = ''
  try {
    project.value = await getProject(projectId.value)
    basicForm.value = {
      name: project.value.name,
      description: project.value.description ?? '',
      status: project.value.status ?? 'draft',
      start_time: project.value.start_time ? project.value.start_time.slice(0, 16) : '',
      end_time: project.value.end_time ? project.value.end_time.slice(0, 16) : '',
      review_end_time: project.value.review_end_time ? project.value.review_end_time.slice(0, 16) : '',
      allow_late_submit: project.value.allow_late_submit ?? false,
      late_submit_deadline: project.value.late_submit_deadline ? project.value.late_submit_deadline.slice(0, 16) : '',
    }
  } catch (e) {
    projectLoadError.value = e.response?.data?.detail ?? '加载项目失败'
    project.value = null
  }
}

async function loadIndicators() {
  if (!projectId.value) return
  indicatorLoading.value = true
  try {
    indicatorTree.value = await getIndicatorTree(projectId.value)
  } catch {
    indicatorTree.value = []
  } finally {
    indicatorLoading.value = false
  }
}

async function loadWeightRule() {
  if (!projectId.value) return
  weightLoading.value = true
  weightError.value = ''
  try {
    const data = await getWeightRule(projectId.value)
    const config = data.formula_config || {}
    // 权重维度仅来自一级指标的 category
    const keys = [...new Set(indicatorTree.value.map((i) => i.category).filter(Boolean))].sort()
    weightKeys.value = keys
    const next = {}
    const defaultVal = keys.length ? parseFloat((1 / keys.length).toFixed(4)) : 0
    keys.forEach((k) => { next[k] = config[k] != null ? Number(config[k]) : defaultVal })
    weightForm.value = next
  } catch {
    weightKeys.value = []
    weightForm.value = {}
  } finally {
    weightLoading.value = false
  }
}

async function loadReviewRule() {
  if (!projectId.value) return
  reviewLoading.value = true
  reviewError.value = ''
  try {
    const data = await getReviewRule(projectId.value)
    reviewForm.value = {
      dual_review_enabled: data.dual_review_enabled ?? true,
      review_scope_mode: data.review_scope_mode ?? 'same_class',
      cross_class_shuffle_enabled: data.cross_class_shuffle_enabled ?? false,
      allowed_assistant_count_per_submission: Number(data.allowed_assistant_count_per_submission ?? 2),
      counselor_participation_mode: data.counselor_participation_mode ?? 'arbitration_only',
      single_review_mode: data.single_review_mode ?? 'assistant_single',
      score_diff_threshold: data.score_diff_threshold != null ? Number(data.score_diff_threshold) : null,
      overall_score_diff_threshold: data.overall_score_diff_threshold != null ? Number(data.overall_score_diff_threshold) : null,
      module_diff_thresholds: data.module_diff_thresholds ? { ...data.module_diff_thresholds } : {},
      final_score_rule: data.final_score_rule ?? 'average',
      allow_view_other_scores: data.allow_view_other_scores ?? false,
      require_arbitration_above_threshold: data.require_arbitration_above_threshold ?? true,
    }
    assignSummary.value = await getProjectAssignmentSummary(projectId.value).catch(() => null)
  } catch {
    // 保持默认
  } finally {
    reviewLoading.value = false
  }
}

// ─── 基本信息保存 ─────────────────────────────────────────────────────────────
async function saveBasic() {
  basicError.value = ''
  basicSaving.value = true
  const form = basicForm.value
  try {
    const payload = {
      name: form.name,
      description: form.description || undefined,
      status: form.status,
      allow_late_submit: form.allow_late_submit,
    }
    if (form.start_time) payload.start_time = new Date(form.start_time).toISOString()
    else payload.start_time = null
    if (form.end_time) payload.end_time = new Date(form.end_time).toISOString()
    else payload.end_time = null
    if (form.review_end_time) payload.review_end_time = new Date(form.review_end_time).toISOString()
    else payload.review_end_time = null
    if (form.allow_late_submit && form.late_submit_deadline) {
      payload.late_submit_deadline = new Date(form.late_submit_deadline).toISOString()
    } else {
      payload.late_submit_deadline = null
    }
    await updateProject(projectId.value, payload)
    project.value = { ...project.value, ...payload }
    goBackToProjects()
  } catch (e) {
    const data = e.response?.data
    basicError.value =
      data?.start_time?.[0] ??
      data?.end_time?.[0] ??
      data?.review_end_time?.[0] ??
      data?.late_submit_deadline?.[0] ??
      data?.status?.[0] ??
      data?.detail ??
      '保存失败'
  } finally {
    basicSaving.value = false
  }
}

// ─── 一级指标操作 ─────────────────────────────────────────────────────────────
function openTopIndicatorCreate() {
  editingTopIndicator.value = null
  topForm.value = {
    name: '',
    category: '',
    agg_formula: 'sum',
    max_score: 100,
    score_source: 'self',
    description: '',
    order: indicatorTree.value.length,
    grade_rules_enabled: false,
    grade_rules_list: [],
    is_record_only: false,
    require_process_record: true,
    record_only_requires_review: false,
  }
  topModalError.value = ''
  topModalOpen.value = true
}

function openTopIndicatorEdit(ind) {
  editingTopIndicator.value = ind
  const existingRules = ind.grade_rules?.rules ?? []
  // 有 grade_rules 时，max_score 字段存的是实际贡献值（已乘系数），回显应使用规则行原始满分最大值
  const rawMaxScoreTop = existingRules.length > 0
    ? (Math.max(...existingRules.map((r) => Number(r.max_score) || 0), 0) || null)
    : ((ind.is_record_only ?? false) ? null : (ind.max_score != null ? Number(ind.max_score) : null))
  topForm.value = {
    name: ind.name,
    category: ind.category ?? '',
    agg_formula: ind.agg_formula ?? 'sum',
    max_score: rawMaxScoreTop,
    // 有子项时评分来源固定为 children（由子项汇总），不允许选其他来源
    score_source: (ind.children?.length) ? 'children' : (ind.score_source === 'reviewer' ? 'self' : (ind.score_source ?? 'self')),
    order: ind.order ?? 0,
    grade_rules_enabled: existingRules.length > 0,
    grade_rules_list: existingRules.map((r) => ({
      min_year: r.min_year ?? 1,
      max_year: r.max_year ?? 5,
      max_score: r.max_score ?? null,
      coefficient: r.coefficient ?? 1,
      label: r.label ?? '',
    })),
    is_record_only: ind.is_record_only ?? false,
    require_process_record: ind.require_process_record !== false,
    record_only_requires_review: ind.record_only_requires_review === true,
  }
  topModalError.value = ''
  topModalOpen.value = true
}

function addTopGradeRule() {
  topForm.value.grade_rules_list.push({ min_year: 1, max_year: 2, max_score: null, coefficient: 1, label: '' })
}

function removeTopGradeRule(idx) {
  topForm.value.grade_rules_list.splice(idx, 1)
}

function closeTopModal() {
  topModalOpen.value = false
  editingTopIndicator.value = null
}

async function submitTopIndicator() {
  topModalError.value = ''
  topSubmitting.value = true
  try {
    // 只在"编辑模式 + sum + 有子项"时才用自动汇总值覆盖用户输入
    // 记录性指标（is_record_only=true）且满分留空 → null（无上限）
    let resolvedMaxScore
    if (topForm.value.agg_formula === 'sum' && editingTopIndicator.value && topFormChildrenSum.value > 0) {
      resolvedMaxScore = topFormChildrenSum.value
    } else if (topForm.value.is_record_only && (topForm.value.max_score === '' || topForm.value.max_score == null)) {
      resolvedMaxScore = null
    } else {
      resolvedMaxScore = topForm.value.max_score ?? 100
    }
    const topGradeRules =
      topForm.value.grade_rules_enabled && topForm.value.grade_rules_list.length
        ? {
            rules: topForm.value.grade_rules_list.map((r) => ({
              min_year: Number(r.min_year),
              max_year: Number(r.max_year),
              max_score: r.max_score !== '' && r.max_score !== null ? Number(r.max_score) : null,
              coefficient: r.coefficient !== '' && r.coefficient !== null ? Number(r.coefficient) : 1,
              label: r.label || '',
            })),
          }
        : {}
    // 年级模式下，存原始满分的最大值（供打分上限使用）；
    // 父级汇总时由后端 _effective_max_score 读取规则行系数计算实际贡献，不依赖此字段。
    const finalMaxScore =
      topForm.value.grade_rules_enabled && topForm.value.grade_rules_list.length
        ? Math.max(...topForm.value.grade_rules_list.map((r) => Number(r.max_score) || 0), 0)
        : resolvedMaxScore
    const body = {
      name: topForm.value.name,
      category: topForm.value.category,
      agg_formula: topForm.value.agg_formula,
      max_score: finalMaxScore,
      score_source: topForm.value.score_source,
      description: topForm.value.description || '',
      order: topForm.value.order ?? 0,
      parent: null,
      grade_rules: topGradeRules,
      is_record_only: topForm.value.is_record_only ?? false,
      require_process_record: topForm.value.require_process_record !== false,
      record_only_requires_review: (topForm.value.is_record_only && topForm.value.score_source === 'self')
        ? (topForm.value.record_only_requires_review === true)
        : false,
    }
    let savedId
    if (editingTopIndicator.value) {
      await updateIndicator(projectId.value, editingTopIndicator.value.id, body)
      savedId = editingTopIndicator.value.id
    } else {
      const created = await createIndicator(projectId.value, body)
      savedId = created?.id ?? null
    }
    lastHighlightIndicatorId.value = savedId
    closeTopModal()
    await loadIndicators()
    loadWeightRule()
  } catch (e) {
    topModalError.value = _extractError(e)
  } finally {
    topSubmitting.value = false
  }
}

// ─── 二级子项操作 ─────────────────────────────────────────────────────────────
function openChildCreate(parent) {
  editingChildIndicator.value = null
  childParent.value = parent
  // 父项为封顶求和时，子项满分继承父项满分（用于显示封顶上限，灰显不可编辑）
  const defaultMaxScore = parent.agg_formula === 'sum_capped' ? (Number(parent.max_score) || 100) : 100
  childForm.value = {
    name: '',
    max_score: defaultMaxScore,
    weight: 1,
    agg_formula: 'sum',
    score_source: 'self',
    description: '',
    order: (parent.children?.length ?? 0),
    grade_rules_enabled: false,
    grade_rules_list: [],
    is_record_only: false,
    require_process_record: true,
    record_only_requires_review: false,
  }
  childModalError.value = ''
  childModalOpen.value = true
}

function openChildEdit(child, parent) {
  editingChildIndicator.value = child
  childParent.value = parent
  const existingRules = child.grade_rules?.rules ?? []
  // 有 grade_rules 时，max_score 字段存的是实际贡献值（已乘系数），回显应使用规则行原始满分最大值
  const rawMaxScoreChild = existingRules.length > 0
    ? (Math.max(...existingRules.map((r) => Number(r.max_score) || 0), 0) || null)
    : (child.max_score != null ? Number(child.max_score) : null)
  childForm.value = {
    name: child.name,
    max_score: (child.is_record_only ?? false) ? null : rawMaxScoreChild,
    weight: Number(child.weight),
    agg_formula: child.agg_formula ?? 'sum',
    // 有下级子项时评分来源固定为 children
    score_source: (child.children?.length) ? 'children' : (child.score_source === 'reviewer' ? 'self' : (child.score_source ?? 'self')),
    description: child.description ?? '',
    order: child.order ?? 0,
    grade_rules_enabled: existingRules.length > 0,
    grade_rules_list: existingRules.map((r) => ({
      min_year: r.min_year ?? 1,
      max_year: r.max_year ?? 5,
      max_score: r.max_score ?? null,
      coefficient: r.coefficient ?? 1,
      label: r.label ?? '',
    })),
    is_record_only: child.is_record_only ?? false,
    require_process_record: child.require_process_record !== false,
    record_only_requires_review: child.record_only_requires_review === true,
  }
  childModalError.value = ''
  childModalOpen.value = true
}

/**
 * 通用编辑入口，由 IndicatorTreeNode 的 edit 事件调用。
 * 根据 node.parent（父级 ID）判断应打开哪个弹窗。
 */
function openEdit(node) {
  if (node.parent === null || node.parent === undefined) {
    // 根节点 → 一级指标表单
    openTopIndicatorEdit(node)
  } else {
    // 子节点 → 子项表单；需要找到父节点对象（用于显示 weight 字段）
    const parentNode = _findNodeById(indicatorTree.value, node.parent)
    openChildEdit(node, parentNode ?? { id: node.parent, agg_formula: 'sum' })
  }
}

/**
 * 在树中按 ID 递归查找节点，返回找到的节点或 null。
 */
function _findNodeById(nodes, id) {
  for (const n of nodes) {
    if (n.id === id) return n
    if (n.children?.length) {
      const found = _findNodeById(n.children, id)
      if (found) return found
    }
  }
  return null
}

function addGradeRule() {
  childForm.value.grade_rules_list.push({ min_year: 1, max_year: 2, max_score: null, coefficient: 1, label: '' })
}

function removeGradeRule(idx) {
  childForm.value.grade_rules_list.splice(idx, 1)
}

function closeChildModal() {
  childModalOpen.value = false
  editingChildIndicator.value = null
  childParent.value = null
}

async function submitChildIndicator() {
  childModalError.value = ''
  childSubmitting.value = true
  try {
    const gradeRules =
      childForm.value.grade_rules_enabled && childForm.value.grade_rules_list.length
        ? {
            rules: childForm.value.grade_rules_list.map((r) => ({
              min_year: Number(r.min_year),
              max_year: Number(r.max_year),
              max_score: r.max_score !== '' && r.max_score !== null ? Number(r.max_score) : null,
              coefficient: r.coefficient !== '' && r.coefficient !== null ? Number(r.coefficient) : 1,
              label: r.label || '',
            })),
          }
        : {}
    // 年级模式下，用各规则 max_score 的最大值作为模型字段（供父级 sum 自动汇总用）
    // 非年级模式下：空字符串（v-model.number 空输入返回 ""）或 null 时按父项类型兜底默认值
    // 记录性子项（is_record_only=true）且不在封顶父项下：允许 null（无上限）
    const isRecordOnly = childForm.value.is_record_only
    const isSumCappedParent = childParent.value?.agg_formula === 'sum_capped'
    const defaultMaxScore = isSumCappedParent
      ? (Number(childParent.value?.max_score) || 100)
      : 100
    let resolvedMaxScore
    if (childForm.value.grade_rules_enabled && childForm.value.grade_rules_list.length) {
      // 存原始满分的最大值（供打分上限使用）；
      // 父级汇总时由后端 _effective_max_score 读取规则行系数计算实际贡献，不依赖此字段。
      resolvedMaxScore = Math.max(
        ...childForm.value.grade_rules_list.map((r) => Number(r.max_score) || 0),
        0,
      )
    } else if (isSumCappedParent) {
      // sum_capped 父项：子项满分用父项满分（灰显只读，不允许留空）
      resolvedMaxScore = Number(childParent.value?.max_score) || 100
    } else if (isRecordOnly && (childForm.value.max_score === '' || childForm.value.max_score == null)) {
      // 记录性子项留空 → 无上限（null）
      resolvedMaxScore = null
    } else {
      resolvedMaxScore = (childForm.value.max_score !== '' && childForm.value.max_score != null)
        ? childForm.value.max_score
        : defaultMaxScore
    }
    const body = {
      name: childForm.value.name,
      max_score: resolvedMaxScore,
      weight: childForm.value.weight ?? 1,
      agg_formula: childForm.value.agg_formula ?? 'sum',
      score_source: childForm.value.score_source,
      description: childForm.value.description || '',
      order: childForm.value.order ?? 0,
      parent: childParent.value.id,
      grade_rules: gradeRules,
      is_record_only: childForm.value.is_record_only ?? false,
      require_process_record: childForm.value.require_process_record !== false,
      record_only_requires_review: (childForm.value.is_record_only && childForm.value.score_source === 'self')
        ? (childForm.value.record_only_requires_review === true)
        : false,
    }
    let savedId
    if (editingChildIndicator.value) {
      await updateIndicator(projectId.value, editingChildIndicator.value.id, body)
      savedId = editingChildIndicator.value.id
    } else {
      const created = await createIndicator(projectId.value, body)
      savedId = created?.id ?? null
    }
    lastHighlightIndicatorId.value = savedId
    closeChildModal()
    await loadIndicators()
  } catch (e) {
    childModalError.value = _extractError(e)
  } finally {
    childSubmitting.value = false
  }
}

// ─── 删除指标 ─────────────────────────────────────────────────────────────────
function confirmDeleteIndicator(ind, isParent) {
  deleteTarget.value = ind
  deleteTargetIsParent.value = isParent
}

async function doDeleteIndicator() {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  deleteError.value = ''
  try {
    await deleteIndicator(projectId.value, deleteTarget.value.id)
    deleteTarget.value = null
    await loadIndicators()
    loadWeightRule()
  } catch (e) {
    deleteError.value = e.response?.data?.detail ?? '删除失败，请稍后重试'
  } finally {
    deleteLoading.value = false
  }
}

// ─── 权重规则保存 ─────────────────────────────────────────────────────────────
async function saveWeight() {
  weightError.value = ''
  const sum = Object.values(weightForm.value).reduce((a, b) => a + b, 0)
  if (Math.abs(sum - 1) > 0.01) {
    weightError.value = '权重之和建议为 1，当前为 ' + sum.toFixed(4)
    return
  }
  weightSaving.value = true
  try {
    await updateWeightRule(projectId.value, {
      formula_type: 'weighted_sum',
      formula_config: { ...weightForm.value },
    })
    goBackToProjects()
  } catch (e) {
    weightError.value = e.response?.data?.detail ?? '保存失败'
  } finally {
    weightSaving.value = false
  }
}

// ─── 评审规则保存 ─────────────────────────────────────────────────────────────
async function saveReview() {
  reviewError.value = ''
  reviewSaving.value = true
  try {
    const moduleThresholds = {}
    Object.entries(reviewForm.value.module_diff_thresholds || {}).forEach(([k, v]) => {
      const key = String(k || '').trim()
      if (!key) return
      if (v === '' || v == null) return
      const num = Number(v)
      if (Number.isNaN(num) || num < 0) return
      moduleThresholds[key] = num
    })
    await updateReviewRule(projectId.value, {
      dual_review_enabled: reviewForm.value.dual_review_enabled,
      review_scope_mode: reviewForm.value.review_scope_mode,
      cross_class_shuffle_enabled: reviewForm.value.cross_class_shuffle_enabled,
      allowed_assistant_count_per_submission: Math.max(2, Number(reviewForm.value.allowed_assistant_count_per_submission || 2)),
      counselor_participation_mode: reviewForm.value.counselor_participation_mode || 'arbitration_only',
      single_review_mode: reviewForm.value.single_review_mode || 'assistant_single',
      score_diff_threshold: reviewForm.value.score_diff_threshold || null,
      overall_score_diff_threshold: reviewForm.value.overall_score_diff_threshold || null,
      module_diff_thresholds: moduleThresholds,
      final_score_rule: reviewForm.value.final_score_rule,
      allow_view_other_scores: reviewForm.value.allow_view_other_scores,
      require_arbitration_above_threshold: reviewForm.value.require_arbitration_above_threshold,
    })
    assignSummary.value = await getProjectAssignmentSummary(projectId.value).catch(() => null)
  } catch (e) {
    reviewError.value = e.response?.data?.detail ?? '保存失败'
  } finally {
    reviewSaving.value = false
  }
}

/**
 * 立即按当前规则生成评审任务分配。
 */
async function generateAssignmentsNow() {
  reviewError.value = ''
  assignGenerating.value = true
  try {
    const res = await generateReviewAssignments(projectId.value)
    assignSummary.value = await getProjectAssignmentSummary(projectId.value).catch(() => null)
    if (res?.detail && res.detail !== 'ok') {
      reviewError.value = `任务生成完成：${res.detail}`
    }
  } catch (e) {
    reviewError.value = e.response?.data?.detail ?? '生成任务失败'
  } finally {
    assignGenerating.value = false
  }
}

/**
 * 清除最近编辑指标的高亮（点击页面任意处触发，弹窗打开时不清除）
 */
function clearHighlight() {
  if (topModalOpen.value || childModalOpen.value || deleteTarget.value) return
  if (lastHighlightIndicatorId.value !== null) lastHighlightIndicatorId.value = null
}

function goBackToProjects() {
  if (project.value?.season) {
    router.push({ name: 'SeasonProjects', params: { seasonId: project.value.season } })
  } else {
    router.push({ name: 'Seasons' })
  }
}

onMounted(async () => {
  seasonList.value = await getSeasons().catch(() => [])
  await loadProject()
  await loadIndicators()
  loadWeightRule()
  loadReviewRule()
  loadTemplateList()
})

useRealtimeRefresh(['project', 'indicator', 'weight_rule', 'review_rule'], () => {
  loadProject()
  loadIndicators()
  loadWeightRule()
  loadReviewRule()
  loadTemplateList()
})

/**
 * 监听子项表单"仅记录存档"开关变化：
 * - 勾选时自动清空 max_score（记录性字段默认无上限）
 * - 取消勾选时，若 max_score 当前为 null，恢复为合理默认值（封顶父项用父项满分，否则 100）
 */
watch(
  () => childForm.value.is_record_only,
  (newVal, oldVal) => {
    if (newVal === oldVal) return
    if (newVal) {
      // 切换为记录性 → 清空上限
      childForm.value.max_score = null
    } else {
      // 取消记录性 → 若当前无上限，恢复默认
      if (childForm.value.max_score === null || childForm.value.max_score === '') {
        childForm.value.max_score =
          childParent.value?.agg_formula === 'sum_capped'
            ? (Number(childParent.value.max_score) || 100)
            : 100
      }
    }
  },
)

/**
 * @description 顶层指标在非“仅记录+学生自评”场景下，强制关闭“推送评阅人复核”。
 */
watch(
  () => [topForm.value.is_record_only, topForm.value.score_source],
  ([isRecordOnly, scoreSource]) => {
    if (!isRecordOnly || scoreSource !== 'self') {
      topForm.value.record_only_requires_review = false
    }
  },
)

/**
 * @description 子项在非“仅记录+学生自评”场景下，强制关闭“推送评阅人复核”。
 */
watch(
  () => [childForm.value.is_record_only, childForm.value.score_source],
  ([isRecordOnly, scoreSource]) => {
    if (!isRecordOnly || scoreSource !== 'self') {
      childForm.value.record_only_requires_review = false
    }
  },
)

watch(projectId, () => {
  loadProject()
  loadIndicators()
  loadWeightRule()
  loadReviewRule()
  loadTemplateList()
})
</script>

