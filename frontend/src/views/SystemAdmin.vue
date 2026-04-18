<template>
  <div class="page-shell">
    <!-- 页面标题（移动端由 Admin.vue 导航条显示） -->
    <div class="hidden md:block">
      <h2 class="text-xl font-semibold text-slate-800">系统管理</h2>
    </div>

    <!-- ═══════════════════════════════════════════
         区块一：补交通道管理（个人/班级精细化）
    ════════════════════════════════════════════ -->
    <section class="order-1 app-surface-strong">
      <div class="border-b border-slate-200 px-3 pt-4 pb-0 md:px-6 md:pt-5">
        <h3 class="mb-3 text-base font-semibold text-slate-800">补交通道管理</h3>
        <!-- 子标签页（移动端可横向滚动） -->
        <div class="flex gap-1 overflow-x-auto scrollbar-hide -mx-1 px-1">
          <button
            v-for="tab in lateChannelTabs"
            :key="tab.key"
            type="button"
            class="rounded-t px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap md:px-4"
            :class="lateTab === tab.key
              ? 'border border-b-white -mb-px border-slate-200 bg-white text-brand-600'
              : 'text-slate-500 hover:text-slate-700'"
            @click="lateTab = tab.key; onLateTabChange(tab.key)"
          >
            {{ tab.label }}
            <span
              v-if="(tab.key === 'requests' && latePendingCount > 0) || (tab.key === 'importRequests' && importPendingCount > 0)"
              class="ml-1 rounded-full bg-red-500 px-1.5 py-0.5 text-xs text-white"
            >{{ tab.key === 'requests' ? latePendingCount : importPendingCount }}</span>
          </button>
        </div>
      </div>

      <div class="p-3 md:p-6">

        <!-- ── 子板块 A：补交申请列表 ── -->
        <div v-if="lateTab === 'requests'">
          <div class="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <p class="text-sm text-slate-500 hidden md:block">学生提交的补交申请，可在此批准（同时开启通道）或拒绝。</p>
            <div class="flex items-center gap-2">
              <select
                v-model="reqFilter"
                class="flex-1 md:flex-none rounded border border-slate-300 bg-white px-2 py-1 text-sm"
                @change="loadLateRequests"
              >
                <option value="">全部</option>
                <option value="pending">待审核</option>
                <option value="approved">已批准</option>
                <option value="rejected">已拒绝</option>
              </select>
              <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" @click="loadLateRequests">刷新</button>
            </div>
          </div>

          <div v-if="lateReqLoading" class="py-8 text-center text-sm text-slate-500">加载中…</div>
          <div v-else-if="lateReqs.length === 0" class="py-8 text-center text-sm text-slate-500">暂无补交申请</div>
          <div v-else class="space-y-2">
            <div class="mobile-card-list">
              <div
                v-for="sub in pendingSubmissions"
                :key="`pending-mobile-${sub.id}`"
                class="mobile-card"
              >
                <div class="flex items-start justify-between gap-2">
                  <label class="inline-flex items-center gap-2 text-sm font-medium text-slate-800">
                    <input type="checkbox" :checked="selectedPendingSubmissionIds.includes(sub.id)" @change="togglePendingSelection(sub.id)" />
                    {{ sub.student_name || '—' }}
                  </label>
                  <span class="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                    {{ sub.status === 'submitted' ? '待推送' : sub.status }}
                  </span>
                </div>
                <div class="mt-1 text-xs text-slate-500">{{ sub.student_no || '—' }}</div>
                <div class="mt-2 space-y-0.5 text-xs text-slate-600">
                  <div>{{ sub.department_name || '—' }} / {{ [sub.major_name || '—', sub.class_grade ? `${sub.class_grade}级` : '', sub.class_name || ''].filter(Boolean).join(' / ') }}</div>
                  <div>{{ sub.season_name || '—' }} / {{ sub.project_name || '—' }}</div>
                  <div>提交：{{ formatDateTime(sub.submitted_at) }}</div>
                </div>
                <button
                  v-if="!isPendingMultiSelectMode"
                  type="button"
                  class="mt-2 app-btn app-btn-secondary app-btn-xs disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="pendingPushLoading"
                  @click="pushSinglePending(sub)"
                >
                  {{ pendingPushLoading ? '推送中…' : '推送此条' }}
                </button>
              </div>
            </div>
            <div class="app-table-wrap hidden md:block">
              <table class="app-table">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="px-3 py-2.5 text-left font-medium">学生</th>
                  <th class="px-3 py-2.5 text-left font-medium">学号</th>
                  <th class="px-3 py-2.5 text-left font-medium">项目</th>
                  <th class="px-3 py-2.5 text-left font-medium">申请理由</th>
                  <th class="px-3 py-2.5 text-left font-medium">佐证材料</th>
                  <th class="px-3 py-2.5 text-left font-medium">状态</th>
                  <th class="px-3 py-2.5 text-left font-medium">申请时间</th>
                  <th class="px-3 py-2.5 text-left font-medium">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="req in lateReqs" :key="req.id" class="hover:bg-slate-50">
                  <td class="px-3 py-2.5 font-medium text-slate-800">{{ req.student_name || '—' }}</td>
                  <td class="px-3 py-2.5 text-slate-600">{{ req.student_no || '—' }}</td>
                  <td class="px-3 py-2.5 max-w-[140px] truncate text-slate-600" :title="req.project_name">{{ req.project_name || '—' }}</td>
                  <td class="px-3 py-2.5 max-w-[180px] truncate text-slate-600" :title="req.reason">{{ req.reason }}</td>
                  <td class="px-3 py-2.5">
                    <div v-if="req.attachments && req.attachments.length > 0" class="space-y-0.5">
                      <a
                        v-for="att in req.attachments"
                        :key="att.id"
                        :href="att.file_url"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="block truncate text-xs text-brand-600 hover:underline max-w-[120px]"
                        :title="att.name"
                      >{{ att.name || '附件' }}</a>
                    </div>
                    <span v-else class="text-xs text-slate-400">无</span>
                  </td>
                  <td class="px-3 py-2.5">
                    <span class="rounded px-2 py-0.5 text-xs font-medium" :class="reqStatusClass(req.status)">
                      {{ req.status_label }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-xs text-slate-500 whitespace-nowrap">{{ formatDateTime(req.created_at) }}</td>
                  <td class="px-3 py-2.5">
                    <template v-if="req.status === 'pending'">
                      <button
                        type="button"
                        class="mr-1 rounded bg-green-600 px-2.5 py-1 text-xs text-white hover:bg-green-700"
                        @click="openApproveDialog(req)"
                      >批准并开通道</button>
                      <button
                        type="button"
                        class="rounded bg-red-100 px-2.5 py-1 text-xs text-red-700 hover:bg-red-200"
                        @click="rejectRequest(req)"
                      >拒绝</button>
                    </template>
                    <span v-else class="text-xs text-slate-400">已处理</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="lateReqError" class="mt-2 text-sm text-red-600">{{ lateReqError }}</p>
        </div>
        </div>

        <!-- ── 子板块 A2：导入权限申请列表 ── -->
        <div v-if="lateTab === 'importRequests'">
          <div class="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <p class="text-sm text-slate-500 hidden md:block">下级在“上级统一导入”策略下提交的导入权限申请。</p>
            <div class="flex items-center gap-2">
              <select
                v-model="importReqFilter"
                class="flex-1 md:flex-none rounded border border-slate-300 bg-white px-2 py-1 text-sm"
                @change="loadImportPermissionRequests"
              >
                <option value="">全部</option>
                <option value="pending">待审核</option>
                <option value="approved">已批准</option>
                <option value="rejected">已拒绝</option>
              </select>
              <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" @click="loadImportPermissionRequests">刷新</button>
            </div>
          </div>
          <div v-if="importReqLoading" class="py-8 text-center text-sm text-slate-500">加载中…</div>
          <div v-else-if="importReqs.length === 0" class="py-8 text-center text-sm text-slate-500">暂无导入权限申请</div>
          <div v-else class="app-table-wrap">
            <table class="app-table">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="px-3 py-2.5 text-left font-medium">申请人</th>
                  <th class="px-3 py-2.5 text-left font-medium">项目</th>
                  <th class="px-3 py-2.5 text-left font-medium">理由</th>
                  <th class="px-3 py-2.5 text-left font-medium">状态</th>
                  <th class="px-3 py-2.5 text-left font-medium">申请时间</th>
                  <th class="px-3 py-2.5 text-left font-medium">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="req in importReqs" :key="req.id" class="hover:bg-slate-50">
                  <td class="px-3 py-2.5 text-slate-700">
                    <div class="font-medium">{{ req.requester_name || '—' }}</div>
                    <div class="text-xs text-slate-500">{{ req.requester_role || '—' }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-slate-600">{{ req.project_name || '—' }}</td>
                  <td class="px-3 py-2.5 max-w-[220px] truncate text-slate-600" :title="req.reason">{{ req.reason || '—' }}</td>
                  <td class="px-3 py-2.5">
                    <span class="rounded px-2 py-0.5 text-xs font-medium" :class="reqStatusClass(req.status)">
                      {{ req.status_label }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-xs text-slate-500 whitespace-nowrap">{{ formatDateTime(req.created_at) }}</td>
                  <td class="px-3 py-2.5">
                    <template v-if="req.status === 'pending'">
                      <button
                        type="button"
                        class="mr-1 rounded bg-green-600 px-2.5 py-1 text-xs text-white hover:bg-green-700"
                        @click="approveImportRequest(req)"
                      >批准</button>
                      <button
                        type="button"
                        class="rounded bg-red-100 px-2.5 py-1 text-xs text-red-700 hover:bg-red-200"
                        @click="rejectImportRequest(req)"
                      >拒绝</button>
                    </template>
                    <span v-else class="text-xs text-slate-400">已处理</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="importReqError" class="mt-2 text-sm text-red-600">{{ importReqError }}</p>
        </div>

        <!-- ── 子板块 B：手动开启补交通道 ── -->
        <div v-if="lateTab === 'open'">
          <p class="mb-4 text-sm text-slate-500">
            补交通道仅针对指定个人或班级开放，不会全局影响其他学生。时长最少 1 小时，学生提交后通道自动关闭。
          </p>
          <form class="space-y-4" @submit.prevent="submitOpenChannel">
            <!-- 范围类型 -->
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700">开放范围 <span class="text-red-500">*</span></label>
              <div class="flex gap-4">
                <label class="flex items-center gap-2 text-sm">
                  <input v-model="openForm.scope_type" type="radio" value="user" /> 指定个人
                </label>
                <label class="flex items-center gap-2 text-sm">
                  <input v-model="openForm.scope_type" type="radio" value="class" /> 指定班级
                </label>
              </div>
            </div>

            <!-- 个人：学号 -->
            <div v-if="openForm.scope_type === 'user'" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">学号 <span class="text-red-500">*</span></label>
                <input
                  v-model="openForm.student_no"
                  type="text"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                  placeholder="请输入学生学号"
                />
                <p class="mt-0.5 text-xs text-slate-400">也可填用户名</p>
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">用户名（如学号不匹配可改填）</label>
                <input
                  v-model="openForm.username"
                  type="text"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                  placeholder="可选，学号优先"
                />
              </div>
            </div>

            <!-- 班级：四级级联选择（院系 → 年级 → 专业 → 班级） -->
            <div v-if="openForm.scope_type === 'class'" class="space-y-3">
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <!-- 院系 -->
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">院系 <span class="text-red-500">*</span></label>
                  <select
                    v-model="openForm.dept_id"
                    class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none"
                    @change="onDeptChangeForClass"
                  >
                    <option :value="null">请选择院系…</option>
                    <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                  </select>
                </div>
                <!-- 年级 -->
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">年级（可选，用于缩小范围）</label>
                  <select
                    v-model="openForm.grade"
                    class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none"
                    :disabled="!openForm.dept_id || availableGrades.length === 0"
                    @change="onGradeOrMajorChange"
                  >
                    <option :value="null">{{ openForm.dept_id ? '不限年级' : '请先选择院系' }}</option>
                    <option v-for="g in availableGrades" :key="g" :value="g">{{ g }}年级</option>
                  </select>
                </div>
                <!-- 专业 -->
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">专业（可选，用于缩小范围）</label>
                  <select
                    v-model="openForm.major_id"
                    class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none"
                    :disabled="!openForm.dept_id || openFormMajors.length === 0"
                    @change="onGradeOrMajorChange"
                  >
                    <option :value="null">{{ openForm.dept_id ? '不限专业' : '请先选择院系' }}</option>
                    <option v-for="m in openFormMajors" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </select>
                </div>
                <!-- 班级 -->
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">班级 <span class="text-red-500">*</span></label>
                  <select
                    v-model="openForm.class_id"
                    class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none"
                    :disabled="!openForm.dept_id || openFormClassLoading"
                  >
                    <option :value="null">
                      {{ !openForm.dept_id ? '请先选择院系' : (openFormClassLoading ? '加载中…' : (filteredClasses.length ? '请选择班级…' : '暂无匹配班级')) }}
                    </option>
                    <option v-for="c in filteredClasses" :key="c.id" :value="c.id">
                      {{ [c.grade ? c.grade + '年级' : '', c.major_name || '', c.name].filter(Boolean).join(' ') }}
                    </option>
                  </select>
                  <p v-if="openForm.dept_id && !openFormClassLoading && filteredClasses.length === 0 && openFormAllClasses.length > 0" class="mt-0.5 text-xs text-amber-600">
                    当前年级/专业条件下无匹配班级，请调整筛选条件
                  </p>
                </div>
              </div>
            </div>

            <!-- 限定项目（可选） -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">限定测评周期（可选）</label>
                <select
                  v-model="openForm.season_id"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none"
                  @change="onSeasonChange"
                >
                  <option :value="null">不限定（对所有项目开放）</option>
                  <option v-for="s in seasons" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>
              <div v-if="openForm.season_id">
                <label class="mb-1 block text-sm font-medium text-slate-700">限定测评项目（可选）</label>
                <select
                  v-model="openForm.project_id"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none"
                >
                  <option :value="null">不限定（该周期所有项目）</option>
                  <option v-for="p in seasonProjects" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
              </div>
            </div>

            <!-- 时长 -->
            <div class="w-full md:w-56">
              <label class="mb-1 block text-sm font-medium text-slate-700">
                开放时长（小时）<span class="text-red-500">*</span>
              </label>
              <input
                v-model.number="openForm.hours"
                type="number"
                min="1"
                max="720"
                class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                placeholder="最少 1 小时"
              />
            </div>

            <!-- 理由 -->
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700">
                开启理由 <span class="text-red-500">*</span>
              </label>
              <textarea
                v-model="openForm.reason"
                rows="3"
                class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                placeholder="请填写开启原因，将留存审计日志…"
              />
            </div>

            <!-- 提交 -->
            <div class="flex items-center gap-4">
              <button
                type="submit"
                class="app-btn app-btn-primary disabled:opacity-50"
                :disabled="openForm.loading"
              >
                {{ openForm.loading ? '开启中…' : '确认开启补交通道' }}
              </button>
              <span v-if="openForm.successMsg" class="text-sm text-green-600">{{ openForm.successMsg }}</span>
              <span v-if="openForm.errorMsg" class="text-sm text-red-600">{{ openForm.errorMsg }}</span>
            </div>
          </form>
        </div>

        <!-- ── 子板块 C：通道列表（仅监控与关闭） ── -->
        <div v-if="lateTab === 'channels'">
          <div class="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <p class="text-sm text-slate-500 hidden md:block">查看通道范围、状态与时效，可在此手动提前关闭通道。</p>
            <div class="flex items-center gap-2">
              <label class="flex items-center gap-1.5 text-sm text-slate-600">
                <input v-model="channelActiveOnly" type="checkbox" @change="loadLateChannels" /> 仅激活中
              </label>
              <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" @click="loadLateChannels">刷新</button>
            </div>
          </div>

          <div v-if="channelLoading" class="py-8 text-center text-sm text-slate-500">加载中…</div>
          <div v-else-if="channels.length === 0" class="py-8 text-center text-sm text-slate-500">
            <div>暂无补交通道记录</div>
            <div v-if="channelActiveOnly" class="mt-1 text-xs text-slate-400">当前仅显示激活中，可取消勾选后查看历史通道</div>
          </div>
          <div v-else>
            <!-- 移动端通道卡片 -->
            <div class="mobile-card-list">
              <div v-for="ch in channels" :key="`ch-mobile-${ch.id}`" class="mobile-card">
                <div class="flex items-center justify-between gap-2 mb-2">
                  <span class="rounded px-2 py-0.5 text-xs font-medium" :class="ch.scope_type === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'">
                    {{ ch.scope_label }}
                  </span>
                  <span v-if="ch.is_active" class="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                    激活中 · 剩 {{ remainingTime(ch.planned_close_at) }}
                  </span>
                  <span v-else class="text-xs text-slate-400">已关闭</span>
                </div>
                <div class="text-sm font-medium text-slate-800">
                  <template v-if="ch.scope_type === 'user'">{{ ch.target_user_name || '—' }} <span class="text-xs text-slate-500 font-normal">{{ ch.target_user_student_no || '' }}</span></template>
                  <template v-else>{{ ch.target_class_name || '—' }}</template>
                </div>
                <div class="mt-1 space-y-0.5 text-xs text-slate-500">
                  <div>项目：{{ ch.project_name || '不限' }}</div>
                  <div>待推送：<span :class="ch.pending_submissions_count > 0 ? 'text-amber-600 font-medium' : ''">{{ ch.pending_submissions_count || 0 }} 条</span></div>
                  <div>开：{{ formatDateTime(ch.open_at) }}</div>
                  <div>关：{{ formatDateTime(ch.planned_close_at) }}</div>
                </div>
                <div v-if="ch.is_active" class="mt-2 border-t border-slate-100 pt-2">
                  <button
                    type="button"
                    class="app-action app-action-danger w-full"
                    :disabled="closingChannelId === ch.id"
                    @click="closeChannel(ch)"
                  >
                    {{ closingChannelId === ch.id ? '关闭中…' : '立即关闭' }}
                  </button>
                </div>
              </div>
            </div>
            <!-- 桌面端通道表格 -->
            <div class="app-table-wrap hidden md:block">
            <table class="app-table">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="px-3 py-2.5 text-left font-medium">范围</th>
                  <th class="px-3 py-2.5 text-left font-medium">目标</th>
                  <th class="px-3 py-2.5 text-left font-medium">限定项目</th>
                  <th class="px-3 py-2.5 text-left font-medium">待推送</th>
                  <th class="px-3 py-2.5 text-left font-medium">理由</th>
                  <th class="px-3 py-2.5 text-left font-medium">开启 / 计划关闭</th>
                  <th class="px-3 py-2.5 text-left font-medium">状态</th>
                  <th class="px-3 py-2.5 text-left font-medium">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="ch in channels" :key="ch.id" class="hover:bg-slate-50">
                  <td class="px-3 py-2.5">
                    <span class="rounded px-2 py-0.5 text-xs font-medium"
                      :class="ch.scope_type === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'">
                      {{ ch.scope_label }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-slate-800">
                    <div v-if="ch.scope_type === 'user'">
                      <div class="font-medium">{{ ch.target_user_name || '—' }}</div>
                      <div class="text-xs text-slate-500">{{ ch.target_user_student_no || '' }}</div>
                    </div>
                    <div v-else>{{ ch.target_class_name || '—' }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-slate-600 text-xs">{{ ch.project_name || '不限' }}</td>
                  <td class="px-3 py-2.5">
                    <span
                      class="rounded px-2 py-0.5 text-xs font-medium"
                      :class="ch.pending_submissions_count > 0 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'"
                    >
                      {{ ch.pending_submissions_count || 0 }} 条
                    </span>
                  </td>
                  <td class="px-3 py-2.5 max-w-[160px] truncate text-slate-600 text-xs" :title="ch.reason">{{ ch.reason }}</td>
                  <td class="px-3 py-2.5 text-xs text-slate-500 whitespace-nowrap">
                    <div>开：{{ formatDateTime(ch.open_at) }}</div>
                    <div>关：{{ formatDateTime(ch.planned_close_at) }}</div>
                    <div v-if="ch.is_active" class="mt-0.5 text-emerald-600 font-medium">
                      剩 {{ remainingTime(ch.planned_close_at) }}
                    </div>
                  </td>
                  <td class="px-3 py-2.5">
                    <span v-if="ch.is_active" class="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">激活中</span>
                    <div v-else class="text-xs text-slate-400 leading-5">
                      <div>已关闭<span v-if="ch.close_reason_label">（{{ ch.close_reason_label }}）</span></div>
                      <div v-if="ch.actual_close_at" class="text-slate-400">
                        {{ formatDateTime(ch.actual_close_at) }}
                      </div>
                    </div>
                  </td>
                  <td class="px-3 py-2.5">
                    <button
                      v-if="ch.is_active"
                      type="button"
                      class="rounded border border-red-300 px-2.5 py-1 text-xs text-red-600 hover:bg-red-50"
                      :disabled="closingChannelId === ch.id"
                      @click="closeChannel(ch)"
                    >
                      {{ closingChannelId === ch.id ? '关闭中…' : '立即关闭' }}
                    </button>
                    <span v-else class="text-xs text-slate-400">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>
          <p v-if="channelError" class="mt-2 text-sm text-red-600">{{ channelError }}</p>
        </div>

        <!-- ── 子板块 D：待推送中心 ── -->
        <div v-if="lateTab === 'push'">
          <div class="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <p class="text-sm text-slate-500">待推送中心仅展示“补交记录池”，不再按通道分组；可按组织与时间筛选后批量推送。</p>
            <div class="flex flex-wrap items-center gap-2">
              <button
                type="button"
                class="app-btn app-btn-secondary app-btn-sm disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="selectedPendingSubmissionIds.length === 0 || pendingPushLoading"
                @click="batchPushSelectedPending"
              >
                {{ pendingPushLoading ? '推送中…' : `批量推送 (${selectedPendingSubmissionIds.length})` }}
              </button>
              <button
                v-if="isPendingMultiSelectMode"
                type="button"
                class="rounded border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50"
                @click="selectedPendingSubmissionIds = []"
              >
                取消多选
              </button>
              <button type="button" class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50" @click="loadLatePendingSubmissions">刷新</button>
            </div>
          </div>

          <div class="mb-3 grid grid-cols-2 gap-2 rounded border border-slate-200 bg-slate-50 p-3 md:grid-cols-4">
            <input
              v-model="pushFilter.keyword"
              type="text"
              class="rounded border border-slate-300 bg-white px-2 py-1 text-sm"
              placeholder="学生姓名或学号"
              @keydown.enter="loadLatePendingSubmissions"
            />
            <select v-model="pushFilter.season_id" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm" @change="onPushFilterSeasonChange">
              <option :value="null">全部周期</option>
              <option v-for="s in seasons" :key="`push-season-${s.id}`" :value="s.id">{{ s.name }}</option>
            </select>
            <select v-model="pushFilter.project_id" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm">
              <option :value="null">全部项目</option>
              <option v-for="p in pushFilterProjects" :key="`push-project-${p.id}`" :value="p.id">{{ p.name }}</option>
            </select>
            <select v-model="pushFilter.department_id" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm" @change="onPushFilterDepartmentChange">
              <option :value="null">全部院系</option>
              <option v-for="d in departments" :key="`push-dept-${d.id}`" :value="d.id">{{ d.name }}</option>
            </select>
            <select v-model="pushFilter.major_id" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm" :disabled="pushFilterMajors.length === 0" @change="onPushFilterMajorChange">
              <option :value="null">全部专业</option>
              <option v-for="m in pushFilterMajors" :key="`push-major-${m.id}`" :value="m.id">{{ m.name }}</option>
            </select>
            <select v-model="pushFilter.class_id" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm" :disabled="pushFilteredClasses.length === 0">
              <option :value="null">全部班级</option>
              <option v-for="c in pushFilteredClasses" :key="`push-class-${c.id}`" :value="c.id">
                {{ [c.grade ? c.grade + '级' : '', c.name].filter(Boolean).join(' ') }}
              </option>
            </select>
            <label class="flex flex-col gap-0.5">
              <span class="text-[11px] text-slate-400 md:hidden">开始日期</span>
              <input v-model.lazy="pushFilter.date_from" type="date" title="开始日期" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm" />
            </label>
            <label class="flex flex-col gap-0.5">
              <span class="text-[11px] text-slate-400 md:hidden">结束日期</span>
              <input v-model.lazy="pushFilter.date_to" type="date" title="结束日期" class="rounded border border-slate-300 bg-white px-2 py-1 text-sm" />
            </label>
            <div class="col-span-2 flex items-center gap-2 md:col-span-1">
              <button type="button" class="flex-1 md:flex-none rounded border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-100" @click="resetPushFilter">重置</button>
              <button type="button" class="flex-1 md:flex-none app-btn app-btn-primary app-btn-sm" @click="loadLatePendingSubmissions">筛选</button>
            </div>
          </div>

          <div v-if="pendingLoading" class="py-8 text-center text-sm text-slate-500">加载中…</div>
          <div v-else-if="pendingSubmissions.length === 0" class="py-8 text-center text-sm text-slate-500">
            暂无可推送记录
          </div>
          <div v-else>
            <!-- 移动端待推送卡片 -->
            <div class="mobile-card-list">
              <div v-for="sub in pendingSubmissions" :key="`push-mobile-${sub.id}`" class="mobile-card">
                <div class="flex items-start justify-between gap-2">
                  <label class="inline-flex items-center gap-2 text-sm font-medium text-slate-800">
                    <input type="checkbox" :checked="selectedPendingSubmissionIds.includes(sub.id)" @change="togglePendingSelection(sub.id)" />
                    {{ sub.student_name || '—' }}
                  </label>
                  <span class="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 flex-shrink-0">待推送</span>
                </div>
                <div class="mt-1 text-xs text-slate-500">{{ sub.student_no || '—' }}</div>
                <div class="mt-2 space-y-0.5 text-xs text-slate-600">
                  <div>{{ sub.department_name || '—' }} / {{ [sub.major_name || '—', sub.class_grade ? `${sub.class_grade}级` : '', sub.class_name || ''].filter(Boolean).join(' / ') }}</div>
                  <div>{{ sub.season_name || '—' }} / {{ sub.project_name || '—' }}</div>
                  <div>提交：{{ formatDateTime(sub.submitted_at) }}</div>
                </div>
                <button
                  v-if="!isPendingMultiSelectMode"
                  type="button"
                  class="mt-2 app-btn app-btn-secondary app-btn-xs w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="pendingPushLoading"
                  @click="pushSinglePending(sub)"
                >
                  {{ pendingPushLoading ? '推送中…' : '推送此条' }}
                </button>
              </div>
            </div>
            <!-- 桌面端待推送表格 -->
            <div class="app-table-wrap hidden md:block">
            <table class="app-table">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="w-8 px-3 py-2.5 text-left font-medium">
                    <input type="checkbox" :checked="isAllPendingSelected" @change="toggleSelectAllPending" />
                  </th>
                  <th class="px-3 py-2.5 text-left font-medium">学生</th>
                  <th class="px-3 py-2.5 text-left font-medium">组织信息</th>
                  <th class="px-3 py-2.5 text-left font-medium">周期 / 项目</th>
                  <th class="px-3 py-2.5 text-left font-medium">提交时间</th>
                  <th class="px-3 py-2.5 text-left font-medium">状态</th>
                  <th class="px-3 py-2.5 text-left font-medium">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="sub in pendingSubmissions" :key="`pending-${sub.id}`" class="hover:bg-slate-50">
                  <td class="px-3 py-2.5">
                    <input type="checkbox" :checked="selectedPendingSubmissionIds.includes(sub.id)" @change="togglePendingSelection(sub.id)" />
                  </td>
                  <td class="px-3 py-2.5 text-slate-800">
                    <div class="font-medium">{{ sub.student_name || '—' }}</div>
                    <div class="text-xs text-slate-500">{{ sub.student_no || '—' }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-slate-600 text-xs">
                    <div>{{ sub.department_name || '—' }}</div>
                    <div>{{ [sub.major_name || '—', sub.class_grade ? `${sub.class_grade}级` : '', sub.class_name || ''].filter(Boolean).join(' / ') }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-slate-600 text-xs">
                    <div>{{ sub.season_name || '—' }}</div>
                    <div>{{ sub.project_name || '—' }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-slate-500 whitespace-nowrap">{{ formatDateTime(sub.submitted_at) }}</td>
                  <td class="px-3 py-2.5">
                    <span class="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {{ sub.status === 'submitted' ? '待推送（已提交）' : sub.status }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5">
                    <button
                      v-if="!isPendingMultiSelectMode"
                      type="button"
                      class="app-btn app-btn-secondary app-btn-xs disabled:opacity-50 disabled:cursor-not-allowed"
                      :disabled="pendingPushLoading"
                      @click="pushSinglePending(sub)"
                    >
                      {{ pendingPushLoading ? '推送中…' : '推送此条' }}
                    </button>
                    <span v-else class="text-xs text-slate-400">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>
          <p v-if="pendingError" class="mt-2 text-sm text-red-600">{{ pendingError }}</p>
          </div>
      </div>
    </section>

    <!-- 批准弹窗 -->
    <Teleport to="body">
      <div
        v-if="approveDialog.show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        @click.self="approveDialog.show = false"
      >
        <div class="app-modal w-full max-w-md">
          <div class="flex items-center justify-between border-b border-slate-200/50 px-6 py-4">
            <h2 class="text-base font-semibold text-slate-800">批准补交申请并开启通道</h2>
            <button type="button" class="text-slate-400 hover:text-slate-600" @click="approveDialog.show = false">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="space-y-4 px-6 py-5">
            <div class="rounded bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <div><strong>学生：</strong>{{ approveDialog.req?.student_name }}（{{ approveDialog.req?.student_no }}）</div>
              <div class="mt-1"><strong>项目：</strong>{{ approveDialog.req?.project_name }}</div>
              <div class="mt-1"><strong>申请理由：</strong>{{ approveDialog.req?.reason }}</div>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700">
                开放时长（小时）<span class="text-red-500">*</span>
              </label>
              <input
                v-model.number="approveDialog.hours"
                type="number"
                min="1"
                max="720"
                class="w-36 rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-slate-700">
                批准说明 / 开启理由 <span class="text-red-500">*</span>
              </label>
              <textarea
                v-model="approveDialog.comment"
                rows="3"
                class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                placeholder="请填写批准原因，将留存审计日志…"
              />
            </div>
            <p v-if="approveDialog.error" class="text-sm text-red-600">{{ approveDialog.error }}</p>
          </div>
          <div class="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
            <button type="button" class="rounded border border-slate-300 px-4 py-1.5 text-sm hover:bg-slate-50" @click="approveDialog.show = false">取消</button>
            <button
              type="button"
              class="rounded bg-green-600 px-5 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
              :disabled="approveDialog.loading"
              @click="confirmApprove"
            >
              {{ approveDialog.loading ? '处理中…' : '确认批准并开通道' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════
         区块二：审计日志
    ════════════════════════════════════════════ -->
    <section class="order-3 app-surface-strong p-4 md:p-6">
      <div class="mb-4 space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="text-base font-semibold text-slate-800">操作日志（本账号）</h3>
            <p class="mt-0.5 text-xs text-slate-400">
              {{ isSuperAdmin ? `仅显示当前${superAdminLabel}账号的操作记录。如需查看所有用户的完整日志，请登录 Django 后台（/admin/）查询。` : `仅显示当前管理员账号的操作记录。导出 CSV 与完整日志需${superAdminLabel}或 Django 后台。` }}
            </p>
          </div>
          <div v-if="isSuperAdmin" class="flex items-center gap-2">
            <button
              type="button"
              class="rounded border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-50"
              :disabled="audit.exportLoading"
              @click="doExportLogs"
            >
              {{ audit.exportLoading ? '导出中…' : '导出 CSV' }}
            </button>
          </div>
        </div>

        <!-- 筛选行 -->
        <div class="space-y-2 md:space-y-0 md:flex md:flex-wrap md:items-center md:gap-2">
          <!-- 等级 + 模块 -->
          <div class="grid grid-cols-2 gap-2 md:contents">
            <select
              v-model="auditFilter.level"
              class="rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:outline-none"
              @change="auditPage = 1; loadAuditLogs()"
            >
              <option value="">全部等级</option>
              <option value="INFO">一般</option>
              <option value="NOTICE">关键</option>
              <option value="WARNING">敏感</option>
              <option value="CRITICAL">高危</option>
            </select>
            <select
              v-model="auditFilter.module"
              class="rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:outline-none"
              @change="auditPage = 1; loadAuditLogs()"
            >
              <option value="">全部模块</option>
              <option value="auth">认证</option>
              <option value="users">用户管理</option>
              <option value="org">组织架构</option>
              <option value="eval">测评管理</option>
              <option value="submission">材料提交</option>
              <option value="scoring">评分</option>
              <option value="appeal">申诉</option>
              <option value="report">报表</option>
              <option value="system">系统</option>
            </select>
          </div>

          <!-- 异常/审计（仅超级管理员） -->
          <template v-if="isSuperAdmin">
            <div class="flex flex-wrap items-center gap-2 md:contents">
              <button
                v-for="opt in abnormalOptions"
                :key="opt.value"
                type="button"
                class="rounded px-3 py-1 text-sm transition-colors"
                :class="auditFilter.isAbnormal === opt.value
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'"
                @click="auditFilter.isAbnormal = opt.value; auditPage = 1; loadAuditLogs()"
              >
                {{ opt.label }}
              </button>
              <label class="flex cursor-pointer items-center gap-1.5 text-sm text-slate-700">
                <input
                  v-model="auditFilter.auditOnly"
                  type="checkbox"
                  class="rounded border-slate-300"
                  @change="auditPage = 1; loadAuditLogs()"
                />
                仅审计事件
              </label>
              <input
                v-model="auditFilter.action"
                type="text"
                class="w-full md:w-36 rounded border border-slate-300 px-2 py-1 text-sm focus:border-brand-500 focus:outline-none"
                placeholder="搜索操作/用户/目标…"
                @keydown.enter="auditPage = 1; loadAuditLogs()"
              />
            </div>
          </template>

          <!-- 日期范围（.lazy 确保 iOS Safari 原生日期选择器能正确同步 v-model） -->
          <div class="grid grid-cols-2 gap-2 md:contents">
            <label class="flex flex-col gap-0.5">
              <span class="text-[11px] text-slate-400 md:hidden">开始日期</span>
              <input
                v-model.lazy="auditFilter.dateFrom"
                type="date"
                title="开始日期"
                class="rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none"
                @change="auditPage = 1; loadAuditLogs()"
              />
            </label>
            <label class="flex flex-col gap-0.5">
              <span class="text-[11px] text-slate-400 md:hidden">结束日期</span>
              <input
                v-model.lazy="auditFilter.dateTo"
                type="date"
                title="结束日期"
                class="rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none"
                @change="auditPage = 1; loadAuditLogs()"
              />
            </label>
          </div>

          <!-- 搜索 + 每页 + 重置 -->
          <div class="flex flex-wrap items-center gap-2 md:contents">
            <button
              type="button"
              class="rounded border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-50"
              @click="auditPage = 1; loadAuditLogs()"
            >
              搜索
            </button>
            <label class="md:ml-auto flex items-center gap-1 text-sm text-slate-600">
              每页
              <select
                v-model.number="auditPageSize"
                class="rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:outline-none"
                @change="onAuditPageSizeChange"
              >
                <option v-for="size in auditPageSizeOptions" :key="size" :value="size">{{ size }}</option>
              </select>
              条
            </label>
            <button
              type="button"
              class="text-sm text-slate-500 hover:text-slate-700 underline"
              @click="resetAuditFilter"
            >
              重置
            </button>
          </div>
        </div>
      </div>

      <div v-if="audit.error" class="mb-3 rounded border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
        {{ audit.error }}
      </div>

      <div v-if="audit.loading" class="py-10 text-center text-sm text-slate-500">加载中…</div>

      <div v-else class="relative">
        <div v-if="audit.paginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60 rounded-xl">
          <span class="text-sm text-slate-400">加载中…</span>
        </div>
        <div v-if="audit.logs.length === 0" class="py-10 text-center text-sm text-slate-500">暂无审计日志</div>
        <div v-else>
          <!-- 移动端审计日志卡片 -->
          <div class="mobile-card-list">
            <div
              v-for="log in audit.logs"
              :key="`log-mobile-${log.id}`"
              class="mobile-card"
              :class="log.is_abnormal ? 'border-red-200 bg-red-50/50' : (log.is_audit_event ? 'border-purple-200 bg-purple-50/50' : '')"
            >
              <div class="flex items-center justify-between gap-2 mb-1">
                <span class="text-xs text-slate-400">#{{ log.id }}</span>
                <div class="flex items-center gap-1.5">
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-medium" :class="levelClass(log.level)">{{ log.level_label || log.level }}</span>
                  <span v-if="log.is_abnormal" class="rounded px-1.5 py-0.5 text-[10px] font-medium bg-red-100 text-red-700">异常</span>
                  <span v-if="log.is_audit_event" class="rounded px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 text-purple-700">审计</span>
                </div>
              </div>
              <div class="text-sm font-medium text-slate-800">{{ log.username_snapshot || '—' }}</div>
              <div class="text-xs text-slate-500">{{ log.role_snapshot || '' }}</div>
              <div class="mt-1.5 space-y-0.5 text-xs text-slate-600">
                <div>{{ log.module_label || log.module }} · {{ log.action_label || log.action || '—' }}</div>
                <div class="truncate">{{ targetSummary(log) }}</div>
                <div class="text-slate-400">{{ formatDateTime(log.created_at) }}</div>
              </div>
              <div class="mt-2 border-t border-slate-100 pt-2">
                <button type="button" class="app-action app-action-default w-full" @click="openLogDetail(log)">查看详情</button>
              </div>
            </div>
          </div>
          <!-- 桌面端审计日志表格 -->
          <div class="app-table-wrap hidden md:block">
          <table class="app-table">
            <thead class="bg-slate-50 text-slate-600">
              <tr>
                <th class="px-3 py-3 text-left font-medium">ID</th>
                <th class="px-3 py-3 text-left font-medium">操作人 / 角色</th>
                <th class="px-3 py-3 text-left font-medium">等级</th>
                <th class="px-3 py-3 text-left font-medium">状态</th>
                <th class="px-3 py-3 text-left font-medium">审计</th>
                <th class="px-3 py-3 text-left font-medium">模块 / 操作</th>
                <th class="px-3 py-3 text-left font-medium">目标</th>
                <th class="px-3 py-3 text-left font-medium">操作时间</th>
                <th class="px-3 py-3 text-left font-medium">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="log in audit.logs"
                :key="log.id"
                :class="log.is_abnormal ? 'bg-red-50 text-red-800' : (log.is_audit_event ? 'bg-purple-50' : 'hover:bg-slate-50')"
              >
                <td class="px-3 py-3 text-slate-500 text-xs">{{ log.id }}</td>
                <td class="px-3 py-3">
                  <div class="font-medium text-slate-800">{{ log.username_snapshot || '—' }}</div>
                  <div class="text-xs text-slate-500">{{ log.role_snapshot || '' }}</div>
                </td>
                <td class="px-3 py-3">
                  <span
                    class="rounded px-2 py-0.5 text-xs font-medium"
                    :class="levelClass(log.level)"
                  >
                    {{ log.level_label || log.level }}
                  </span>
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                  <span
                    v-if="log.is_abnormal"
                    class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700"
                  >
                    <span>⚠</span> 异常
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700"
                  >
                    <span>✓</span> 正常
                  </span>
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                  <span
                    v-if="log.is_audit_event"
                    class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700"
                  >
                    <span>★</span> 是
                  </span>
                  <span
                    v-else
                    class="text-xs text-slate-400"
                  >—</span>
                </td>
                <td class="px-3 py-3">
                  <div class="text-xs text-slate-500">{{ log.module_label || log.module }}</div>
                  <div>{{ log.action_label || log.action || '—' }}</div>
                </td>
                <td class="max-w-xs px-3 py-3 relative group">
                  <span class="block truncate text-slate-600 text-xs cursor-default">
                    {{ targetSummary(log) }}
                  </span>
                  <!-- 悬浮详情气泡：显示完整目标名和具体变更字段 -->
                  <div
                    v-if="log.target_repr || log.extra?.changed"
                    class="pointer-events-none absolute left-0 top-full z-30 mt-0.5 hidden w-72 rounded border border-slate-200 bg-white p-2.5 text-xs shadow-lg group-hover:block"
                  >
                    <div v-if="log.target_repr" class="font-medium text-slate-700 break-all mb-1">
                      {{ log.target_repr }}
                    </div>
                    <template v-if="log.extra?.changed && Object.keys(log.extra.changed).length">
                      <div class="text-slate-500 mb-0.5">变更字段：</div>
                      <div
                        v-for="(v, k) in log.extra.changed"
                        :key="k"
                        class="text-slate-600 leading-relaxed"
                      >
                        <span class="font-medium">{{ k }}</span>：{{ v.old || '（空）' }} → {{ v.new || '（空）' }}
                      </div>
                    </template>
                  </div>
                </td>
                <td class="px-3 py-3 text-slate-600 text-xs whitespace-nowrap">{{ formatDateTime(log.created_at) }}</td>
                <td class="px-3 py-3">
                  <button
                    type="button"
                    class="rounded border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
                    @click="openLogDetail(log)"
                  >
                    详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="audit.totalCount > auditPageSize" class="mt-4 flex items-center justify-between text-sm text-slate-600">
          <span>共 {{ audit.totalCount }} 条</span>
          <div class="flex gap-2">
            <button
              type="button"
              class="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50 disabled:opacity-40"
              :disabled="auditPage <= 1"
              @click="auditPage--; loadAuditLogs(true)"
            >上一页</button>
            <span class="px-2 py-1">{{ auditPage }} / {{ auditTotalPages }}</span>
            <button
              type="button"
              class="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50 disabled:opacity-40"
              :disabled="auditPage >= auditTotalPages"
              @click="auditPage++; loadAuditLogs(true)"
            >下一页</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
         区块三：管理员改分
    ════════════════════════════════════════════ -->
    <section class="order-2 app-surface-strong p-4 md:p-6">
      <h3 class="mb-1 text-base font-semibold text-slate-800">管理员改分</h3>
      <p class="mb-4 text-sm text-slate-500">
        改分操作将写入审计日志（异常标记），须填写理由留痕，不可撤销，请谨慎操作。
      </p>

      <form class="space-y-4" @submit.prevent="submitScoreOverride">
        <!-- 提交 ID -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">
            提交 ID <span class="text-red-500">*</span>
          </label>
          <input
            v-model.number="override.submissionId"
            type="number"
            min="1"
            class="w-full md:w-48 rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            placeholder="请输入提交 ID"
          />
          <p v-if="override.errors.submissionId" class="mt-1 text-xs text-red-600">{{ override.errors.submissionId }}</p>
        </div>

        <!-- 新分数 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">
            新最终分数 <span class="text-red-500">*</span>
          </label>
          <input
            v-model.number="override.finalScore"
            type="number"
            min="0"
            max="100"
            step="0.01"
            class="w-full md:w-48 rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            placeholder="0 ~ 100"
          />
          <p v-if="override.errors.finalScore" class="mt-1 text-xs text-red-600">{{ override.errors.finalScore }}</p>
        </div>

        <!-- 改分理由 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">
            改分理由 <span class="text-red-500">*</span>（必须留痕）
          </label>
          <textarea
            v-model="override.reason"
            rows="3"
            class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            placeholder="请详细填写改分理由，此记录将永久保存…"
          />
          <p v-if="override.errors.reason" class="mt-1 text-xs text-red-600">{{ override.errors.reason }}</p>
        </div>

        <!-- 改分凭证文件 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">上传改分凭证（可选）</label>
          <input
            ref="overrideFileInput"
            type="file"
            accept="image/*,.pdf,.doc,.docx"
            class="block w-full text-sm text-slate-600
              file:mr-3 file:rounded file:border file:border-slate-300
              file:bg-slate-50 file:px-3 file:py-1.5 file:text-sm
              file:text-slate-700 hover:file:bg-slate-100"
            @change="onOverrideFileChange"
          />
          <p v-if="override.fileName" class="mt-1 text-xs text-slate-500">已选：{{ override.fileName }}</p>
        </div>

        <!-- 提交按钮 & 状态 -->
            <div class="flex flex-col gap-2 md:flex-row md:items-center md:gap-4">
              <button
                type="submit"
                class="w-full md:w-auto rounded bg-amber-600 px-5 py-2 text-sm text-white hover:bg-amber-700 disabled:opacity-50"
                :disabled="override.loading"
              >
                {{ override.loading ? '提交中…' : '确认改分' }}
              </button>
          <span v-if="override.successMsg" class="text-sm text-green-600">{{ override.successMsg }}</span>
          <span v-if="override.errorMsg" class="text-sm text-red-600">{{ override.errorMsg }}</span>
        </div>
      </form>
    </section>

    <!-- ═══════════════════════════════════════════
         审计日志详情弹窗
    ════════════════════════════════════════════ -->
    <Teleport to="body">
      <div
        v-if="logDetail.show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        @click.self="closeLogDetail"
      >
        <div class="app-modal w-full max-w-lg">
          <!-- 弹窗标题 -->
          <div class="flex items-center justify-between border-b border-slate-200/50 px-6 py-4">
            <h2 class="text-base font-semibold text-slate-800">
              审计日志详情
              <span v-if="logDetail.data?.is_abnormal" class="ml-2 rounded bg-red-100 px-2 py-0.5 text-xs text-red-700">⚠ 异常操作</span>
            </h2>
            <button
              type="button"
              class="text-slate-400 hover:text-slate-600"
              @click="closeLogDetail"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- 弹窗内容 -->
          <div v-if="logDetail.loading" class="py-10 text-center text-sm text-slate-500">加载中…</div>
          <div v-else-if="logDetail.data" class="space-y-3 px-6 py-5 text-sm">
            <div class="grid grid-cols-3 gap-x-4 gap-y-3">
              <div>
                <p class="text-xs text-slate-500">日志 ID</p>
                <p class="font-medium text-slate-800">{{ logDetail.data.id }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">操作人 / 角色</p>
                <p class="font-medium text-slate-800">{{ logDetail.data.username_snapshot || logDetail.data.operator_name || '—' }}</p>
                <p class="text-xs text-slate-500">{{ logDetail.data.role_snapshot || '' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">操作时间</p>
                <p class="font-medium text-slate-800">{{ formatDateTime(logDetail.data.created_at) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">等级 / 模块</p>
                <p class="font-medium text-slate-800">
                  <span :class="levelClass(logDetail.data.level)" class="rounded px-1.5 py-0.5 text-xs">
                    {{ logDetail.data.level_label || logDetail.data.level }}
                  </span>
                  · {{ logDetail.data.module_label || logDetail.data.module }}
                </p>
              </div>
              <div>
                <p class="text-xs text-slate-500">操作</p>
                <p class="font-medium text-slate-800">{{ logDetail.data.action_label || logDetail.data.action }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">目标类型</p>
                <p class="font-medium text-slate-800">{{ logDetail.data.target_type || '—' }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-500">目标ID / 描述</p>
                <p class="font-medium text-slate-800">
                  {{ logDetail.data.target_id ?? '' }}
                  <span v-if="logDetail.data.target_repr" class="text-slate-600"> · {{ logDetail.data.target_repr }}</span>
                </p>
              </div>
              <div>
                <p class="text-xs text-slate-500">审计事件</p>
                <p :class="logDetail.data.is_audit_event ? 'text-purple-700 font-semibold' : 'text-slate-400'">
                  {{ logDetail.data.is_audit_event ? '是' : '否' }}
                </p>
              </div>
            </div>

            <!-- 理由 -->
            <div v-if="logDetail.data.reason">
              <p class="mb-1 text-xs text-slate-500">操作理由</p>
              <p class="rounded bg-slate-50 px-3 py-2 text-slate-700">{{ logDetail.data.reason }}</p>
            </div>

            <!-- 附加信息 JSON -->
            <div v-if="logDetail.data.extra_pretty">
              <p class="mb-1 text-xs text-slate-500">附加信息</p>
              <pre class="overflow-auto rounded bg-slate-50 px-3 py-2 text-xs text-slate-700 max-h-40">{{ logDetail.data.extra_pretty }}</pre>
            </div>

            <!-- 佐证附件列表 -->
            <div v-if="logDetail.data.attachments && logDetail.data.attachments.length > 0">
              <p class="mb-1 text-xs text-slate-500">佐证材料</p>
              <ul class="space-y-1">
                <li
                  v-for="att in logDetail.data.attachments"
                  :key="att.id"
                  class="flex items-center gap-2"
                >
                  <a
                    :href="att.file_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-brand-600 hover:underline text-xs"
                  >
                    {{ att.file_name }}
                  </a>
                  <span class="text-xs text-slate-400">（{{ formatFileSize(att.file_size) }}）</span>
                  <!-- 图片预览 -->
                  <div v-if="isImageUrl(att.file_url)" class="mt-1">
                    <img
                      :src="att.file_url"
                      alt="凭证图片"
                      class="max-h-48 rounded border border-slate-200 object-contain"
                    />
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div class="border-t border-slate-200 px-6 py-3 text-right">
            <button
              type="button"
              class="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
              @click="closeLogDetail"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
/**
 * 系统管理页（模块8）：
 *   1. 补交通道管理（个人/班级精细化：申请列表 / 手动开启 / 活跃通道管理）
 *   2. 审计日志（按 is_abnormal / action 筛选；异常行高亮；可查看详情弹窗）
 *   3. 管理员改分（submission_id + final_score + reason 必填，evidence_file 可选）
 */
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  getLateRequests, handleLateRequest, getLateChannels, createLateChannel, closeLateChannel,
  getLatePendingSubmissions, batchPushPendingSubmissions,
  getImportPermissionRequests, handleImportPermissionRequest,
  getAuditLogs, getAuditLogDetail, getMyLogs, getMyLogDetail, scoreOverride, exportAuditLogs,
} from '@/api/admin'
import { getSeasons, getSeasonProjects } from '@/api/eval'
import { useAuthStore } from '@/stores/auth'
import { useRoleMetaStore } from '@/stores/roles'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'
import { openAlert, openConfirm, openPrompt } from '@/utils/dialog'

const auth = useAuthStore()
const roleMeta = useRoleMetaStore()
roleMeta.ensureLoaded()
const superAdminLabel = computed(() => roleMeta.nameByLevel(5))
/** 仅超级管理员可访问 audit/logs 与导出；管理员使用 my-logs 查看本人记录 */
const isSuperAdmin = computed(() => auth.isSuperAdmin)

/* ─────────────── 补交通道子标签 ─────────────── */
const lateChannelTabs = [
  { key: 'requests', label: '补交申请' },
  { key: 'importRequests', label: '导入权限申请' },
  { key: 'open',     label: '手动开启通道' },
  { key: 'channels', label: '通道列表' },
  { key: 'push',     label: '待推送中心' },
]
const lateTab = ref('requests')
const latePendingCount = ref(0)
const importPendingCount = ref(0)

/**
 * 切换补交通道子标签时自动加载对应数据
 * @param {string} key
 */
function onLateTabChange(key) {
  if (key === 'requests') loadLateRequests()
  else if (key === 'importRequests') loadImportPermissionRequests()
  else if (key === 'channels') {
    channelActiveOnly.value = true
    loadLateChannels()
  } else if (key === 'push') {
    loadLatePendingSubmissions()
  }
}

/* ─────────────── 导入权限申请列表 ─────────────── */
const importReqs = ref([])
const importReqLoading = ref(false)
const importReqError = ref('')
const importReqFilter = ref('pending')

async function loadImportPermissionRequests() {
  importReqLoading.value = true
  importReqError.value = ''
  try {
    const data = await getImportPermissionRequests(importReqFilter.value ? { status: importReqFilter.value } : {})
    importReqs.value = Array.isArray(data) ? data : (data?.results ?? [])
    importPendingCount.value = importReqs.value.filter((r) => r.status === 'pending').length
  } catch (e) {
    importReqError.value = e.response?.data?.detail ?? '加载导入权限申请失败'
  } finally {
    importReqLoading.value = false
  }
}

async function approveImportRequest(req) {
  const { confirmed } = await openConfirm({
    title: '批准申请确认',
    message: `确认批准 ${req.requester_name} 的导入权限申请？`,
    confirmText: '确认批准',
  })
  if (!confirmed) return
  try {
    await handleImportPermissionRequest(req.id, { action: 'approve' })
    await loadImportPermissionRequests()
  } catch (e) {
    await openAlert({
      title: '操作失败',
      message: e.response?.data?.detail ?? '操作失败',
      danger: true,
    })
  }
}

async function rejectImportRequest(req) {
  const input = await openPrompt({
    title: '拒绝申请',
    message: '请输入拒绝说明：',
    inputPlaceholder: '请填写拒绝原因',
    inputRequired: true,
  })
  if (!input?.confirmed) return
  const comment = String(input.value || '').trim()
  if (!comment) return
  try {
    await handleImportPermissionRequest(req.id, { action: 'reject', comment })
    await loadImportPermissionRequests()
  } catch (e) {
    await openAlert({
      title: '操作失败',
      message: e.response?.data?.detail ?? '操作失败',
      danger: true,
    })
  }
}

/* ─────────────── 补交申请列表 ─────────────── */
const lateReqs = ref([])
const lateReqLoading = ref(false)
const lateReqError = ref('')
const reqFilter = ref('pending')

/** 加载补交申请列表 */
async function loadLateRequests() {
  lateReqLoading.value = true
  lateReqError.value = ''
  try {
    const data = await getLateRequests(reqFilter.value ? { status: reqFilter.value } : {})
    lateReqs.value = Array.isArray(data) ? data : (data?.results ?? [])
    latePendingCount.value = lateReqs.value.filter((r) => r.status === 'pending').length
  } catch (e) {
    lateReqError.value = e.response?.data?.detail ?? '加载补交申请失败'
  } finally {
    lateReqLoading.value = false
  }
}

/**
 * 申请状态对应的 CSS class
 * @param {string} s
 */
function reqStatusClass(s) {
  return {
    pending:  'bg-amber-100 text-amber-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  }[s] ?? 'bg-slate-100 text-slate-600'
}

/** 拒绝申请 */
async function rejectRequest(req) {
  const { confirmed } = await openConfirm({
    title: '拒绝申请确认',
    message: `确认拒绝 ${req.student_name} 的补交申请？`,
    confirmText: '确认拒绝',
    danger: true,
  })
  if (!confirmed) return
  try {
    await handleLateRequest(req.id, { action: 'reject', comment: '管理员拒绝' })
    await loadLateRequests()
  } catch (e) {
    await openAlert({
      title: '操作失败',
      message: e.response?.data?.detail ?? '操作失败',
      danger: true,
    })
  }
}

/* ─────────────── 批准弹窗 ─────────────── */
const approveDialog = reactive({
  show: false,
  req: null,
  hours: 24,
  comment: '',
  loading: false,
  error: '',
})

/**
 * 打开批准弹窗
 * @param {Object} req
 */
function openApproveDialog(req) {
  approveDialog.req = req
  approveDialog.hours = 24
  approveDialog.comment = ''
  approveDialog.error = ''
  approveDialog.show = true
}

/** 确认批准，同时开启补交通道 */
async function confirmApprove() {
  approveDialog.error = ''
  if (!approveDialog.comment.trim()) {
    approveDialog.error = '请填写批准说明'
    return
  }
  if (!approveDialog.hours || approveDialog.hours < 1) {
    approveDialog.error = '时长至少 1 小时'
    return
  }
  approveDialog.loading = true
  try {
    await handleLateRequest(approveDialog.req.id, {
      action: 'approve',
      comment: approveDialog.comment.trim(),
      hours: approveDialog.hours,
    })
    approveDialog.show = false
    await loadLateRequests()
  } catch (e) {
    approveDialog.error = e.response?.data?.detail ?? '操作失败，请重试'
  } finally {
    approveDialog.loading = false
  }
}

/* ─────────────── 手动开启通道 ─────────────── */
const seasons = ref([])
const seasonProjects = ref([])
const departments = ref([])
const openFormAllClasses = ref([])   // 选定院系后加载的全量班级（用于派生年级列表 + 前端筛选）
const openFormMajors = ref([])       // 选定院系后加载的专业列表
const openFormClassLoading = ref(false)

const openForm = reactive({
  scope_type: 'user',
  student_no: '',
  username: '',
  dept_id: null,
  grade: null,
  major_id: null,
  class_id: null,
  season_id: null,
  project_id: null,
  hours: 24,
  reason: '',
  loading: false,
  successMsg: '',
  errorMsg: '',
})

/** 年级选项：从已加载的班级中去重提取，按字符串排序 */
const availableGrades = computed(() =>
  [...new Set(openFormAllClasses.value.map((c) => c.grade).filter(Boolean))].sort()
)

/** 当前过滤后的班级列表（院系已限定，再叠加年级/专业筛选） */
const filteredClasses = computed(() => {
  let list = openFormAllClasses.value
  if (openForm.grade) list = list.filter((c) => c.grade === openForm.grade)
  if (openForm.major_id) list = list.filter((c) => c.major === openForm.major_id)
  return list
})

/** 加载院系列表（用于班级级联选择） */
async function loadDepartments() {
  try {
    const { data } = await api.get('/departments/')
    departments.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    departments.value = []
  }
}

/**
 * 院系变更：同时加载该院系下的全部班级（用于年级派生）和全部专业，重置下级选项
 */
async function onDeptChangeForClass() {
  openForm.grade = null
  openForm.major_id = null
  openForm.class_id = null
  openFormAllClasses.value = []
  openFormMajors.value = []
  if (!openForm.dept_id) return
  openFormClassLoading.value = true
  try {
    const [classRes, majorRes] = await Promise.all([
      api.get('/classes/', { params: { department: openForm.dept_id } }),
      api.get('/majors/', { params: { department: openForm.dept_id } }),
    ])
    openFormAllClasses.value = Array.isArray(classRes.data) ? classRes.data : (classRes.data?.results ?? [])
    openFormMajors.value = Array.isArray(majorRes.data) ? majorRes.data : (majorRes.data?.results ?? [])
  } catch {
    openFormAllClasses.value = []
    openFormMajors.value = []
  } finally {
    openFormClassLoading.value = false
  }
}

/**
 * 年级或专业变更时重置班级选择（filteredClasses 由 computed 自动重算）
 */
function onGradeOrMajorChange() {
  openForm.class_id = null
}

/** 加载测评周期列表（用于项目选择） */
async function loadSeasons() {
  try {
    seasons.value = await getSeasons()
  } catch {
    seasons.value = []
  }
}

/** 切换周期时加载对应项目 */
async function onSeasonChange() {
  openForm.project_id = null
  seasonProjects.value = []
  if (!openForm.season_id) return
  try {
    seasonProjects.value = await getSeasonProjects(openForm.season_id)
  } catch {
    seasonProjects.value = []
  }
}

/** 提交手动开启补交通道 */
async function submitOpenChannel() {
  openForm.successMsg = ''
  openForm.errorMsg = ''
  if (!openForm.reason.trim()) {
    openForm.errorMsg = '请填写开启理由'
    return
  }
  if (!openForm.hours || openForm.hours < 1) {
    openForm.errorMsg = '时长至少 1 小时'
    return
  }
  if (openForm.scope_type === 'user' && !openForm.student_no.trim() && !openForm.username.trim()) {
    openForm.errorMsg = '请填写学号或用户名'
    return
  }
  if (openForm.scope_type === 'class' && !openForm.class_id) {
    openForm.errorMsg = '请选择目标班级'
    return
  }
  openForm.loading = true
  try {
    const body = {
      scope_type: openForm.scope_type,
      reason: openForm.reason.trim(),
      hours: openForm.hours,
    }
    if (openForm.scope_type === 'user') {
      if (openForm.student_no.trim()) body.student_no = openForm.student_no.trim()
      else body.username = openForm.username.trim()
    } else {
      body.class_id = openForm.class_id
    }
    if (openForm.project_id) body.project_id = openForm.project_id
    await createLateChannel(body)
    openForm.successMsg = '补交通道已成功开启！'
    openForm.student_no = ''
    openForm.username = ''
    openForm.dept_id = null
    openForm.grade = null
    openForm.major_id = null
    openForm.class_id = null
    openForm.season_id = null
    openForm.project_id = null
    openForm.hours = 24
    openForm.reason = ''
    seasonProjects.value = []
    openFormAllClasses.value = []
    openFormMajors.value = []
  } catch (e) {
    openForm.errorMsg = e.response?.data?.detail ?? '开启失败，请检查参数'
  } finally {
    openForm.loading = false
  }
}

/* ─────────────── 通道列表 ─────────────── */
const channels = ref([])
const channelLoading = ref(false)
const channelError = ref('')
const channelActiveOnly = ref(true)
const closingChannelId = ref(null)

/** 加载补交通道列表 */
async function loadLateChannels() {
  channelLoading.value = true
  channelError.value = ''
  try {
    const params = channelActiveOnly.value ? { active_only: '1' } : {}
    const data = await getLateChannels(params)
    channels.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch (e) {
    const status = e?.response?.status
    if (status === 401 || status === 403) {
      channelError.value = '无权限或登录已过期，请重新登录后重试'
    } else if (!e?.response) {
      channelError.value = '网络异常，无法连接服务端，请检查网络后重试'
    } else {
      channelError.value = e.response?.data?.detail ?? '加载通道列表失败'
    }
  } finally {
    channelLoading.value = false
  }
}

/**
 * 待推送中心：扁平记录池
 */
const pendingSubmissions = ref([])
const pendingLoading = ref(false)
const pendingError = ref('')
const pendingPushLoading = ref(false)
const selectedPendingSubmissionIds = ref([])
const pushFilterProjects = ref([])
const pushFilterMajors = ref([])
const pushFilterAllClasses = ref([])
const pushFilter = reactive({
  keyword: '',
  season_id: null,
  project_id: null,
  department_id: null,
  major_id: null,
  class_id: null,
  date_from: '',
  date_to: '',
})

const pushFilteredClasses = computed(() => {
  if (!pushFilter.major_id) return pushFilterAllClasses.value
  return pushFilterAllClasses.value.filter((c) => c.major === pushFilter.major_id)
})

const isAllPendingSelected = computed(() => {
  if (pendingSubmissions.value.length === 0) return false
  const selectedSet = new Set(selectedPendingSubmissionIds.value)
  return pendingSubmissions.value.every((sub) => selectedSet.has(sub.id))
})
const isPendingMultiSelectMode = computed(() => selectedPendingSubmissionIds.value.length > 0)

async function onPushFilterSeasonChange() {
  pushFilter.project_id = null
  pushFilterProjects.value = []
  if (!pushFilter.season_id) return
  try {
    pushFilterProjects.value = await getSeasonProjects(pushFilter.season_id)
  } catch {
    pushFilterProjects.value = []
  }
}

async function onPushFilterDepartmentChange() {
  pushFilter.major_id = null
  pushFilter.class_id = null
  pushFilterMajors.value = []
  pushFilterAllClasses.value = []
  if (!pushFilter.department_id) return
  try {
    const [majorRes, classRes] = await Promise.all([
      api.get('/majors/', { params: { department: pushFilter.department_id } }),
      api.get('/classes/', { params: { department: pushFilter.department_id } }),
    ])
    pushFilterMajors.value = Array.isArray(majorRes.data) ? majorRes.data : (majorRes.data?.results ?? [])
    pushFilterAllClasses.value = Array.isArray(classRes.data) ? classRes.data : (classRes.data?.results ?? [])
  } catch {
    pushFilterMajors.value = []
    pushFilterAllClasses.value = []
  }
}

function onPushFilterMajorChange() {
  pushFilter.class_id = null
}

function resetPushFilter() {
  pushFilter.keyword = ''
  pushFilter.season_id = null
  pushFilter.project_id = null
  pushFilter.department_id = null
  pushFilter.major_id = null
  pushFilter.class_id = null
  pushFilter.date_from = ''
  pushFilter.date_to = ''
  pushFilterProjects.value = []
  pushFilterMajors.value = []
  pushFilterAllClasses.value = []
  selectedPendingSubmissionIds.value = []
  loadLatePendingSubmissions()
}

async function loadLatePendingSubmissions() {
  pendingLoading.value = true
  pendingError.value = ''
  try {
    const params = {}
    if (pushFilter.keyword.trim()) params.keyword = pushFilter.keyword.trim()
    if (pushFilter.season_id) params.season_id = pushFilter.season_id
    if (pushFilter.project_id) params.project_id = pushFilter.project_id
    if (pushFilter.department_id) params.department_id = pushFilter.department_id
    if (pushFilter.major_id) params.major_id = pushFilter.major_id
    if (pushFilter.class_id) params.class_id = pushFilter.class_id
    if (pushFilter.date_from) params.date_from = pushFilter.date_from
    if (pushFilter.date_to) params.date_to = pushFilter.date_to
    const data = await getLatePendingSubmissions(params)
    pendingSubmissions.value = Array.isArray(data) ? data : (data?.results ?? [])
    const validIds = new Set(pendingSubmissions.value.map((sub) => sub.id))
    selectedPendingSubmissionIds.value = selectedPendingSubmissionIds.value.filter((id) => validIds.has(id))
  } catch (e) {
    pendingError.value = e.response?.data?.detail ?? '加载待推送记录失败'
    pendingSubmissions.value = []
  } finally {
    pendingLoading.value = false
  }
}

function togglePendingSelection(submissionId) {
  const idx = selectedPendingSubmissionIds.value.indexOf(submissionId)
  if (idx >= 0) selectedPendingSubmissionIds.value.splice(idx, 1)
  else selectedPendingSubmissionIds.value.push(submissionId)
}

function toggleSelectAllPending() {
  if (isAllPendingSelected.value) {
    selectedPendingSubmissionIds.value = []
    return
  }
  selectedPendingSubmissionIds.value = pendingSubmissions.value.map((sub) => sub.id)
}

async function pushSinglePending(sub) {
  const { confirmed } = await openConfirm({
    title: '推送确认',
    message: `确认推送 ${sub.student_name}（${sub.student_no || '无学号'}）这条补交记录到评审流程吗？`,
    confirmText: '确认推送',
  })
  if (!confirmed) return
  pendingPushLoading.value = true
  try {
    const result = await batchPushPendingSubmissions([sub.id])
    await openAlert({
      title: '操作结果',
      message: result.detail ?? `已推送 ${result.pushed_count ?? 0} 条记录`,
    })
    await loadLatePendingSubmissions()
  } catch (e) {
    await openAlert({
      title: '推送失败',
      message: e.response?.data?.detail ?? '推送失败，请重试',
      danger: true,
    })
  } finally {
    pendingPushLoading.value = false
  }
}

async function batchPushSelectedPending() {
  if (selectedPendingSubmissionIds.value.length === 0) {
    await openAlert({
      title: '请选择记录',
      message: '请先勾选待推送记录',
      danger: true,
    })
    return
  }
  const { confirmed } = await openConfirm({
    title: '批量推送确认',
    message: `确认批量推送已选的 ${selectedPendingSubmissionIds.value.length} 条补交记录吗？`,
    confirmText: '确认推送',
  })
  if (!confirmed) return
  pendingPushLoading.value = true
  try {
    const result = await batchPushPendingSubmissions(selectedPendingSubmissionIds.value)
    await openAlert({
      title: '操作结果',
      message: result.detail ?? `已推送 ${result.pushed_count ?? 0} 条记录`,
    })
    selectedPendingSubmissionIds.value = []
    await loadLatePendingSubmissions()
  } catch (e) {
    await openAlert({
      title: '批量推送失败',
      message: e.response?.data?.detail ?? '批量推送失败，请重试',
      danger: true,
    })
  } finally {
    pendingPushLoading.value = false
  }
}

/**
 * 手动关闭补交通道
 * @param {Object} ch
 */
async function closeChannel(ch) {
  const target = ch.target_user_name ?? ch.target_class_name ?? `通道#${ch.id}`
  const { confirmed } = await openConfirm({
    title: '关闭通道确认',
    message: `确认立即关闭 ${target} 的补交通道？`,
    confirmText: '确认关闭',
    danger: true,
  })
  if (!confirmed) return
  closingChannelId.value = ch.id
  try {
    await closeLateChannel(ch.id, '管理员手动关闭')
    await loadLateChannels()
  } catch (e) {
    await openAlert({
      title: '关闭失败',
      message: e.response?.data?.detail ?? '关闭失败',
      danger: true,
    })
  } finally {
    closingChannelId.value = null
  }
}


/**
 * 计算剩余时间的可读字符串
 * @param {string} expiresAt - ISO 日期字符串
 * @returns {string}
 */
function remainingTime(expiresAt) {
  if (!expiresAt) return '—'
  const diff = new Date(expiresAt) - Date.now()
  if (diff <= 0) return '已过期'
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

/* ─────────────── 操作日志 ─────────────── */
const auditPage = ref(1)
const auditPageSize = ref(20)
const auditPageSizeOptions = [10, 20, 50, 100]
const auditFilter = reactive({
  isAbnormal: 'all',
  auditOnly: false,
  level: '',
  module: '',
  action: '',
  dateFrom: '',
  dateTo: '',
})

const audit = reactive({
  loading: false,
  paginating: false,
  exportLoading: false,
  error: '',
  logs: [],
  totalCount: 0,
})

const auditTotalPages = computed(() => Math.max(1, Math.ceil(audit.totalCount / auditPageSize.value)))

const abnormalOptions = [
  { value: 'all', label: '全部' },
  { value: 1, label: '仅异常' },
  { value: 0, label: '仅正常' },
]

/** 等级对应的 CSS class */
function levelClass(level) {
  const map = {
    INFO:     'bg-slate-100 text-slate-600',
    NOTICE:   'bg-blue-100 text-blue-700',
    WARNING:  'bg-amber-100 text-amber-700',
    CRITICAL: 'bg-red-100 text-red-700',
  }
  return map[level] ?? 'bg-slate-100 text-slate-600'
}

/**
 * 目标列摘要文本：若 extra.changed 存在则在目标名后附加变更字段列表，
 * 超出宽度时通过 CSS truncate 截断，悬浮气泡会显示完整内容。
 */
function targetSummary(log) {
  const repr = log.target_repr || (log.target_type ? `${log.target_type}#${log.target_id}` : '—')
  const changed = log.extra?.changed
  if (changed && Object.keys(changed).length) {
    return `${repr}（改: ${Object.keys(changed).join('、')}）`
  }
  return repr
}

/** 构建当前过滤条件的 params 对象（超级管理员用 audit/logs） */
function buildAuditParams() {
  const params = { page: auditPage.value, page_size: auditPageSize.value }
  if (auditFilter.isAbnormal !== 'all') params.is_abnormal = auditFilter.isAbnormal
  if (auditFilter.auditOnly) params.is_audit_event = 1
  if (auditFilter.level) params.level = auditFilter.level
  if (auditFilter.module) params.module = auditFilter.module
  if (auditFilter.action.trim()) params.action = auditFilter.action.trim()
  if (auditFilter.dateFrom) params.date_from = auditFilter.dateFrom
  if (auditFilter.dateTo) params.date_to = auditFilter.dateTo
  return params
}

/** 构建本人操作日志查询参数（管理员用 my-logs，仅支持 level/module/date） */
function buildMyLogParams() {
  const params = { page: auditPage.value, page_size: auditPageSize.value }
  if (auditFilter.level) params.level = auditFilter.level
  if (auditFilter.module) params.module = auditFilter.module
  if (auditFilter.dateFrom) params.date_from = auditFilter.dateFrom
  if (auditFilter.dateTo) params.date_to = auditFilter.dateTo
  return params
}

/** 重置过滤条件并重新加载 */
function resetAuditFilter() {
  auditFilter.isAbnormal = 'all'
  auditFilter.auditOnly = false
  auditFilter.level = ''
  auditFilter.module = ''
  auditFilter.action = ''
  auditFilter.dateFrom = ''
  auditFilter.dateTo = ''
  auditPage.value = 1
  loadAuditLogs()
}

/** 切换审计分页条数后回到第一页并刷新。 */
function onAuditPageSizeChange() {
  auditPage.value = 1
  loadAuditLogs()
}

/**
 * 加载操作日志列表：超级管理员用 audit/logs，管理员用 my-logs
 * @param {boolean} [soft=false] - 翻页时使用软加载
 */
async function loadAuditLogs(soft = false) {
  if (soft) {
    audit.paginating = true
  } else {
    audit.loading = true
  }
  audit.error = ''
  try {
    const data = isSuperAdmin.value
      ? await getAuditLogs(buildAuditParams())
      : await getMyLogs(buildMyLogParams())
    if (Array.isArray(data)) {
      audit.logs = data
      audit.totalCount = data.length
    } else {
      audit.logs = data.results ?? []
      audit.totalCount = data.count ?? audit.logs.length
    }
  } catch (e) {
    audit.error = e.response?.data?.detail ?? '加载操作日志失败'
    audit.logs = []
  } finally {
    audit.loading = false
    audit.paginating = false
  }
}

/** 导出操作日志 CSV（仅超级管理员可调用后端导出接口） */
async function doExportLogs() {
  if (!isSuperAdmin.value) {
    await openAlert({
      title: '无权限',
      message: `仅${superAdminLabel.value}可导出操作日志`,
      danger: true,
    })
    return
  }
  audit.exportLoading = true
  try {
    const params = buildAuditParams()
    delete params.page
    const response = await exportAuditLogs(params)
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8-sig' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const now = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    a.download = `operation_log_${now}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    await openAlert({
      title: '导出失败',
      message: e.response?.data?.detail ?? '导出失败，请重试',
      danger: true,
    })
  } finally {
    audit.exportLoading = false
  }
}

/* ─────────────── 审计日志详情弹窗 ─────────────── */
const logDetail = reactive({
  show: false,
  loading: false,
  data: null,
})

/**
 * 打开审计日志详情弹窗，优先用列表已有数据，再请求完整详情
 * 超级管理员用 audit/logs/:id，管理员用 my-logs/:id
 * @param {Object} log - 列表行数据
 */
async function openLogDetail(log) {
  logDetail.show = true
  logDetail.data = log
  logDetail.loading = true
  try {
    const detail = isSuperAdmin.value
      ? await getAuditLogDetail(log.id)
      : await getMyLogDetail(log.id)
    logDetail.data = detail
  } catch (e) {
    // 若详情接口失败，保留列表行数据降级展示
  } finally {
    logDetail.loading = false
  }
}

/** 关闭详情弹窗 */
function closeLogDetail() {
  logDetail.show = false
  logDetail.data = null
}

/**
 * 判断 URL 是否指向图片
 * @param {string} url
 * @returns {boolean}
 */
function isImageUrl(url) {
  if (!url) return false
  return /\.(jpg|jpeg|png|gif|webp|bmp)(\?.*)?$/i.test(url)
}

/**
 * 格式化文件大小
 * @param {number} bytes
 * @returns {string}
 */
function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/* ─────────────── 管理员改分 ─────────────── */
const overrideFileInput = ref(null)
const override = reactive({
  submissionId: '',
  finalScore: '',
  reason: '',
  file: null,
  fileName: '',
  loading: false,
  successMsg: '',
  errorMsg: '',
  errors: { submissionId: '', finalScore: '', reason: '' },
})

/**
 * 处理改分凭证文件选择
 * @param {Event} e
 */
function onOverrideFileChange(e) {
  const file = e.target.files?.[0] ?? null
  override.file = file
  override.fileName = file?.name ?? ''
}

/** 校验改分表单 */
function validateOverride() {
  override.errors.submissionId = ''
  override.errors.finalScore = ''
  override.errors.reason = ''
  let ok = true
  if (!override.submissionId) {
    override.errors.submissionId = '请输入提交 ID'
    ok = false
  }
  if (override.finalScore === '' || override.finalScore === null) {
    override.errors.finalScore = '请输入新分数'
    ok = false
  } else if (Number(override.finalScore) < 0 || Number(override.finalScore) > 100) {
    override.errors.finalScore = '分数范围为 0 ~ 100'
    ok = false
  }
  if (!override.reason.trim()) {
    override.errors.reason = '改分理由不能为空（必须留痕）'
    ok = false
  }
  return ok
}

/** 提交管理员改分 */
async function submitScoreOverride() {
  if (!validateOverride()) return
  override.loading = true
  override.successMsg = ''
  override.errorMsg = ''
  try {
    await scoreOverride({
      submission_id: override.submissionId,
      final_score: override.finalScore,
      reason: override.reason.trim(),
      evidence_file: override.file ?? undefined,
    })
    override.successMsg = `提交 #${override.submissionId} 分数已修改为 ${override.finalScore}，改分记录已留痕。`
    override.submissionId = ''
    override.finalScore = ''
    override.reason = ''
    override.file = null
    override.fileName = ''
    if (overrideFileInput.value) overrideFileInput.value.value = ''
    await loadAuditLogs()
  } catch (e) {
    const data = e.response?.data
    override.errorMsg =
      data?.detail ??
      data?.submission_id?.[0] ??
      data?.final_score?.[0] ??
      data?.reason?.[0] ??
      '提交失败，请重试'
  } finally {
    override.loading = false
  }
}

useRealtimeRefresh('late_request', loadLateRequests)
useRealtimeRefresh('audit_log', loadAuditLogs)

onMounted(() => {
  loadLateRequests()
  loadImportPermissionRequests()
  loadSeasons()
  loadDepartments()
  loadAuditLogs()
})
</script>
