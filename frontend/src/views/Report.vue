<template>
  <div class="page-shell">
    <h2 class="app-page-title">成绩报表</h2>

    <!-- ===================== 学生视图：我的成绩 ===================== -->
    <template v-if="isStudent">
      <div v-if="myLoading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
      <div v-else-if="myError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ myError }}</div>
      <template v-else>
        <div v-if="myReport.length === 0" class="app-surface py-12 text-center text-slate-500">暂无成绩记录</div>
        <button
          v-for="item in myReport"
          :key="item.submission.id"
          type="button"
          class="app-surface-strong w-full overflow-hidden text-left transition hover:-translate-y-0.5 hover:shadow-md"
          @click="goSubmissionDetail(item.submission.id)"
        >
          <div class="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-5 py-3">
            <div>
              <span class="font-medium text-slate-800">{{ item.submission.project_name || '—' }}</span>
              <span class="ml-3 text-sm text-slate-500">{{ statusLabel(item) }}</span>
            </div>
            <div class="text-right">
              <span class="text-sm text-slate-500">最终得分</span>
              <span class="ml-2 text-xl font-bold" :class="item.final_score != null ? 'text-brand-700' : 'text-slate-400'">
                {{ item.final_score != null ? item.final_score : '未评分' }}
              </span>
            </div>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm text-slate-600">
            <div class="flex flex-wrap gap-x-8 gap-y-1">
              <span>提交 ID：{{ item.submission.id }}</span>
              <span>提交时间：{{ formatDateTime(item.submission.submitted_at) }}</span>
            </div>
            <span class="text-xs font-medium text-brand-600">点击查看模块详情与申诉入口</span>
          </div>
        </button>
      </template>
    </template>

    <!-- ===================== 主任 / 管理员视图：项目报表 ===================== -->
    <template v-else-if="isDirectorOrAdmin">
      <!-- 筛选区域 -->
      <div class="app-surface p-4">
        <!-- 第一行：周期 + 项目 + 院系 + 专业 -->
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">测评周期</label>
            <select
              v-model="selectedSeasonId"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onSeasonChange"
            >
              <option value="">请选择周期</option>
              <option v-for="s in sortedSeasons" :key="s.id" :value="s.id">{{ s.name }}{{ s.status === 'ongoing' ? '（进行中）' : s.status === 'closed' ? '（已结束）' : '' }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">测评项目</label>
            <select
              v-model="selectedProjectId"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              :disabled="!selectedSeasonId || projects.length === 0"
              @change="onProjectChange"
            >
              <option value="">请选择项目</option>
              <option v-for="p in sortedProjects" :key="p.id" :value="p.id">{{ p.name }}{{ p.status === 'ongoing' ? '（进行中）' : p.status === 'closed' ? '（已结束）' : '' }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">院系筛选</label>
            <select
              v-model="reportFilters.department_id"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onDepartmentFilterChange"
            >
              <option value="">全部院系</option>
              <option v-for="d in departmentOptions" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">专业筛选</label>
            <select
              v-model="reportFilters.major_id"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onMajorFilterChange"
            >
              <option value="">全部专业</option>
              <option v-for="m in majorOptions" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>
        </div>

        <!-- 第二行：班级 + 人员搜索 + 操作按钮 -->
        <div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">班级筛选</label>
            <select
              v-model="reportFilters.class_id"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="">全部班级</option>
              <option v-for="c in classOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">人员筛选</label>
            <input
              v-model.trim="reportFilters.search"
              type="text"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="姓名/学号/用户名"
              @keyup.enter="applyReportFilters"
            />
          </div>
          <div v-if="selectedProjectId" class="flex items-end gap-2">
            <button
              type="button"
              class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              @click="applyReportFilters"
            >应用筛选</button>
            <button
              type="button"
              class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              @click="resetReportFilters"
            >重置筛选</button>
          </div>
          <div v-if="selectedProjectId" class="flex items-end">
            <button
              type="button"
              class="w-full rounded border border-brand-500 bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-100"
              @click="openExportConfig"
            >导出模板配置</button>
          </div>
        </div>

        <!-- 第三行：快捷导出（仅在选了项目时显示） -->
        <div v-if="selectedProjectId" class="mt-3 flex flex-wrap items-center gap-3 rounded border border-slate-200 bg-slate-50 px-4 py-3">
          <span class="shrink-0 text-xs text-slate-500">快捷导出（按当前筛选）：</span>
          <select v-model="pageExportFormat" class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm" @change="onPageExportFormatChange">
            <option value="xlsx">Excel</option>
            <option value="word">Word</option>
            <option value="pdf">PDF</option>
          </select>
          <select v-model="pageExportMappingId" class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">
            <option :value="null">使用系统默认映射</option>
            <option v-for="item in pageExportMappingCandidates" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <label v-if="pageExportFormat !== 'xlsx'" class="flex cursor-pointer items-center gap-1.5 text-xs text-slate-600">
            <input v-model="pageExportMultiFile" type="checkbox" class="cursor-pointer" />
            每人单独文件（ZIP）
          </label>
          <select v-if="pageExportFormat !== 'xlsx' && pageExportMultiFile"
                  v-model="pageExportGroupBy"
                  class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">
            <option value="">不分组（平铺）</option>
            <option value="class">按班级子目录</option>
          </select>
          <button
            type="button"
            class="rounded border border-green-600 bg-green-50 px-4 py-1.5 text-sm font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
            :disabled="exporting"
            @click="doPageDrivenExport"
          >{{ exporting ? '导出中…' : '导出' }}</button>
          <span v-if="exportError" class="text-sm text-red-600">{{ exportError }}</span>
        </div>
      </div>

      <!-- 报表内容 -->
      <template v-if="selectedProjectId">
        <div v-if="reportLoading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
        <div v-else-if="reportError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ reportError }}</div>
        <template v-else>
          <!-- 汇总：按班级 -->
          <div class="app-surface-strong overflow-hidden">
            <div class="border-b border-slate-100 px-5 py-3">
              <h3 class="font-medium text-slate-800">班级汇总</h3>
              <p class="mt-0.5 text-xs text-slate-500">共 {{ summary?.total_count ?? 0 }} 份有效成绩</p>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full border-collapse text-sm">
                <thead>
                  <tr class="border-b border-slate-200 bg-slate-50">
                    <th class="px-4 py-2.5 text-left font-medium text-slate-700">班级</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">人数</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">平均分</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">合计分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(cls, name) in summary?.by_class"
                    :key="name"
                    class="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td class="px-4 py-2.5 text-slate-800">{{ name }}</td>
                    <td class="px-4 py-2.5 text-right text-slate-800">{{ cls.count }}</td>
                    <td class="px-4 py-2.5 text-right text-slate-800">{{ cls.avg?.toFixed(2) ?? '—' }}</td>
                    <td class="px-4 py-2.5 text-right text-slate-800">{{ cls.total?.toFixed(2) ?? '—' }}</td>
                  </tr>
                  <tr v-if="!summary?.by_class || Object.keys(summary.by_class).length === 0">
                    <td colspan="4" class="px-4 py-8 text-center text-slate-500">暂无汇总数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 排名列表 -->
          <div class="app-surface-strong relative overflow-hidden">
            <div v-if="rankingPaginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60">
              <span class="text-sm text-slate-400">加载中…</span>
            </div>
            <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3">
              <h3 class="font-medium text-slate-800">总分排名</h3>
              <span class="text-xs text-slate-500">共 {{ ranking?.total ?? 0 }} 条</span>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full border-collapse text-sm">
                <thead>
                  <tr class="border-b border-slate-200 bg-slate-50">
                    <th class="px-4 py-2.5 text-left font-medium text-slate-700">排名</th>
                    <th class="px-4 py-2.5 text-left font-medium text-slate-700">学号</th>
                    <th class="px-4 py-2.5 text-left font-medium text-slate-700">姓名</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">最终得分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in ranking?.results"
                    :key="row.submission_id"
                    class="border-b border-slate-100 hover:bg-slate-50"
                    :class="row.rank <= 3 ? 'bg-amber-50' : ''"
                  >
                    <td class="px-4 py-2.5">
                      <span
                        class="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
                        :class="rankBadgeClass(row.rank)"
                      >{{ row.rank }}</span>
                    </td>
                    <td class="px-4 py-2.5 text-slate-600">{{ row.student_no || row.username }}</td>
                    <td class="px-4 py-2.5 text-slate-800">{{ row.real_name || row.username }}</td>
                    <td class="px-4 py-2.5 text-right font-medium text-slate-800">{{ row.final_score ?? '—' }}</td>
                  </tr>
                  <tr v-if="!ranking?.results?.length">
                    <td colspan="4" class="px-4 py-8 text-center text-slate-500">暂无排名数据</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页 -->
            <div v-if="ranking && ranking.total > rankingPageSize" class="flex items-center justify-between border-t border-slate-100 px-5 py-3">
              <span class="text-sm text-slate-500">
                第 {{ rankingPage }} / {{ totalPages }} 页，共 {{ ranking.total }} 条
              </span>
              <div class="flex gap-2">
                <button
                  type="button"
                  class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                  :disabled="rankingPage <= 1"
                  @click="gotoRankingPage(rankingPage - 1)"
                >上一页</button>
                <button
                  type="button"
                  class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                  :disabled="rankingPage >= totalPages"
                  @click="gotoRankingPage(rankingPage + 1)"
                >下一页</button>
              </div>
            </div>
          </div>
        </template>
      </template>

      <!-- 未选项目时的提示 -->
      <div v-else class="app-surface py-12 text-center text-slate-500">
        请先选择测评周期和项目以查看报表
      </div>
    </template>

    <!-- ===================== 辅导员/评审视图：负责班级报表 ===================== -->
    <template v-else-if="isCounselor">
      <!-- 筛选区域 -->
      <div class="app-surface p-4">
        <p class="mb-3 text-xs text-slate-500">当前视图仅展示您负责班级的成绩数据。</p>
        <!-- 第一行：周期 + 项目 + 院系 + 专业 -->
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">测评周期</label>
            <select
              v-model="selectedSeasonId"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onSeasonChange"
            >
              <option value="">请选择周期</option>
              <option v-for="s in sortedSeasons" :key="s.id" :value="s.id">{{ s.name }}{{ s.status === 'ongoing' ? '（进行中）' : s.status === 'closed' ? '（已结束）' : '' }}</option>
            </select>
          </div>
          <div v-if="selectedSeasonId">
            <label class="mb-1 block text-xs font-medium text-slate-500">测评项目</label>
            <select
              v-model="selectedProjectId"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onProjectChange"
            >
              <option value="">请选择项目</option>
              <option v-for="p in sortedProjects" :key="p.id" :value="p.id">{{ p.name }}{{ p.status === 'ongoing' ? '（进行中）' : p.status === 'closed' ? '（已结束）' : '' }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">院系筛选</label>
            <select
              v-model="reportFilters.department_id"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onDepartmentFilterChange"
            >
              <option value="">全部院系</option>
              <option v-for="d in departmentOptions" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">专业筛选</label>
            <select
              v-model="reportFilters.major_id"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              @change="onMajorFilterChange"
            >
              <option value="">全部专业</option>
              <option v-for="m in majorOptions" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>
        </div>

        <!-- 第二行：班级 + 人员 + 操作按钮 -->
        <div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">班级筛选</label>
            <select
              v-model="reportFilters.class_id"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
            >
              <option value="">全部班级</option>
              <option v-for="c in classOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">人员筛选</label>
            <input
              v-model.trim="reportFilters.search"
              type="text"
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none"
              placeholder="姓名/学号/用户名"
              @keyup.enter="applyReportFilters"
            />
          </div>
          <div v-if="selectedProjectId" class="flex items-end gap-2">
            <button
              type="button"
              class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              @click="applyReportFilters"
            >应用筛选</button>
            <button
              type="button"
              class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              @click="resetReportFilters"
            >重置筛选</button>
          </div>
          <div v-if="selectedProjectId" class="flex items-end">
            <button
              type="button"
              class="w-full rounded border border-brand-500 px-3 py-2 text-sm text-brand-700 hover:bg-brand-50"
              @click="openExportConfig"
            >导出模板配置</button>
          </div>
        </div>

        <!-- 快捷导出 -->
        <div v-if="selectedProjectId" class="mt-3 flex flex-wrap items-center gap-3 rounded border border-slate-200 bg-slate-50 px-4 py-3">
          <span class="shrink-0 text-xs text-slate-500">快捷导出（按当前筛选）：</span>
          <select v-model="pageExportFormat" class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm" @change="onPageExportFormatChange">
            <option value="xlsx">Excel</option>
            <option value="word">Word</option>
            <option value="pdf">PDF</option>
          </select>
          <select v-model="pageExportMappingId" class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">
            <option :value="null">使用系统默认映射</option>
            <option v-for="item in pageExportMappingCandidates" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <label v-if="pageExportFormat !== 'xlsx'" class="flex cursor-pointer items-center gap-1.5 text-xs text-slate-600">
            <input v-model="pageExportMultiFile" type="checkbox" class="cursor-pointer" />
            每人单独文件（ZIP）
          </label>
          <select v-if="pageExportFormat !== 'xlsx' && pageExportMultiFile"
                  v-model="pageExportGroupBy"
                  class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">
            <option value="">不分组（平铺）</option>
            <option value="class">按班级子目录</option>
          </select>
          <button
            type="button"
            class="rounded border border-green-600 bg-green-50 px-4 py-1.5 text-sm font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
            :disabled="exporting"
            @click="doPageDrivenExport"
          >{{ exporting ? '导出中…' : '导出' }}</button>
          <span v-if="exportError" class="text-sm text-red-600">{{ exportError }}</span>
        </div>
      </div>

      <template v-if="selectedProjectId">
        <div v-if="reportLoading" class="app-surface py-12 text-center text-slate-500">加载中…</div>
        <div v-else-if="reportError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ reportError }}</div>
        <template v-else>
          <!-- 汇总：按班级 -->
          <div v-if="summary && Object.keys(summary.by_class || {}).length > 0" class="app-surface-strong overflow-hidden">
            <div class="border-b border-slate-100 px-5 py-3">
              <h3 class="font-medium text-slate-800">负责班级汇总</h3>
              <p class="mt-0.5 text-xs text-slate-500">共 {{ summary.total_count ?? 0 }} 份有效成绩</p>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full border-collapse text-sm">
                <thead>
                  <tr class="border-b border-slate-200 bg-slate-50">
                    <th class="px-4 py-2.5 text-left font-medium text-slate-700">班级</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">人数</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">平均分</th>
                    <th class="px-4 py-2.5 text-right font-medium text-slate-700">合计分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(cls, name) in summary.by_class" :key="name" class="border-b border-slate-100 hover:bg-slate-50">
                    <td class="px-4 py-2.5 text-slate-800">{{ name }}</td>
                    <td class="px-4 py-2.5 text-right text-slate-800">{{ cls.count }}</td>
                    <td class="px-4 py-2.5 text-right text-slate-800">{{ cls.avg?.toFixed(2) ?? '—' }}</td>
                    <td class="px-4 py-2.5 text-right text-slate-800">{{ cls.total?.toFixed(2) ?? '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 排名列表 -->
          <div v-if="ranking" class="app-surface-strong relative">
            <div v-if="rankingPaginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60">
              <span class="text-sm text-slate-400">加载中…</span>
            </div>
            <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3">
              <h3 class="font-medium text-slate-800">负责班级学生排名</h3>
              <span class="text-xs text-slate-500">共 {{ ranking?.total ?? 0 }} 条</span>
            </div>
            <table class="w-full text-sm">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="px-4 py-3 text-left">排名</th>
                  <th class="px-4 py-3 text-left">学号</th>
                  <th class="px-4 py-3 text-left">用户名</th>
                  <th class="px-4 py-3 text-right">总分</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="item in ranking.results" :key="item.submission_id" class="hover:bg-slate-50">
                  <td class="px-4 py-3">
                    <span class="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold" :class="rankBadgeClass(item.rank)">{{ item.rank }}</span>
                  </td>
                  <td class="px-4 py-3 text-slate-700">{{ item.student_no || '—' }}</td>
                  <td class="px-4 py-3 text-slate-700">{{ item.username }}</td>
                  <td class="px-4 py-3 text-right font-medium text-slate-800">{{ item.final_score ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
            <!-- 分页 -->
            <div v-if="ranking.total > rankingPageSize" class="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm text-slate-600">
              <span>共 {{ ranking.total }} 条</span>
              <div class="flex gap-2">
                <button type="button" class="rounded border border-slate-300 px-3 py-1 disabled:opacity-40" :disabled="rankingPage <= 1" @click="gotoRankingPage(rankingPage - 1)">上一页</button>
                <span class="px-2 py-1">{{ rankingPage }} / {{ totalPages }}</span>
                <button type="button" class="rounded border border-slate-300 px-3 py-1 disabled:opacity-40" :disabled="rankingPage >= totalPages" @click="gotoRankingPage(rankingPage + 1)">下一页</button>
              </div>
            </div>
          </div>
        </template>
      </template>
      <div v-else class="app-surface py-12 text-center text-slate-500">
        请先选择测评周期和项目以查看班级报表
      </div>
    </template>

    <!-- 未识别角色 -->
    <template v-else>
      <div class="app-surface py-12 text-center text-slate-500">
        当前角色暂无独立报表视图，如需查看成绩请切换至学生角色。
      </div>
    </template>

    <div v-if="exportConfigVisible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div class="flex max-h-[92vh] w-full max-w-5xl flex-col rounded-xl bg-white shadow-xl">

        <!-- 标题栏 -->
        <div class="flex items-center justify-between border-b px-5 py-3">
          <h3 class="text-base font-semibold text-slate-800">导出模板与映射配置</h3>
          <button type="button" class="text-sm text-slate-500 hover:text-slate-700" @click="closeExportConfig">关闭</button>
        </div>

        <!-- 基础配置行 -->
        <div class="border-b bg-slate-50 px-5 py-3 space-y-2">
          <div class="flex flex-wrap items-center gap-3">
            <select v-model="selectedMappingId" class="rounded border px-2 py-1.5 text-sm" @change="applySelectedMapping">
              <option :value="null">新建映射配置</option>
              <option v-for="item in mappingList" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
            <input v-model.trim="mappingForm.name" type="text" class="w-40 rounded border px-2 py-1.5 text-sm" placeholder="映射名称" />
            <select v-model="mappingForm.output_format" class="rounded border px-2 py-1.5 text-sm">
              <option value="xlsx">Excel</option>
              <option value="word">Word</option>
              <option value="pdf">PDF</option>
            </select>
            <label class="flex items-center gap-1.5 text-sm text-slate-700">
              <input v-model="mappingForm.is_default" type="checkbox" />
              设为默认
            </label>
            <button
              type="button"
              class="flex items-center gap-1 rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-600 hover:bg-white"
              @click="templatePanelOpen = !templatePanelOpen"
            >
              <span>{{ selectedTemplateId ? templateList.find(t => t.id === selectedTemplateId)?.name || '模板已选' : '选择/上传模板' }}</span>
              <span class="text-slate-400">{{ templatePanelOpen ? '▲' : '▼' }}</span>
            </button>
          </div>

          <!-- 模板管理折叠面板 -->
          <div v-if="templatePanelOpen" class="rounded border bg-white p-3 space-y-2">
            <div class="grid gap-2 sm:grid-cols-4">
              <input v-model.trim="templateForm.name" type="text" class="rounded border px-2 py-1.5 text-sm" placeholder="模板名称" />
              <select v-model="templateForm.template_type" class="rounded border px-2 py-1.5 text-sm">
                <option value="word">Word 模板</option>
                <option value="excel">Excel 模板</option>
              </select>
              <select v-model="templateForm.visibility" class="rounded border px-2 py-1.5 text-sm">
                <option value="private">仅自己可见</option>
                <option v-if="isDirectorOrAdmin" value="department">院系可见</option>
                <option v-if="isDirectorOrAdmin" value="global">全局可见</option>
              </select>
              <input type="file" class="text-sm" @change="onTemplateFileChange" />
            </div>
            <button type="button" class="rounded border border-brand-500 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50" :disabled="uploadingTemplate" @click="uploadTemplate">
              {{ uploadingTemplate ? '上传中…' : '上传模板' }}
            </button>
            <div class="max-h-32 overflow-auto rounded border">
              <button
                v-for="item in templateList"
                :key="item.id"
                type="button"
                class="flex w-full items-center justify-between border-b px-3 py-2 text-left text-sm hover:bg-slate-50"
                :class="selectedTemplateId === item.id ? 'bg-brand-50 font-medium text-brand-700' : ''"
                @click="selectedTemplateId = item.id; templatePanelOpen = false"
              >
                <span class="truncate">{{ item.name }}</span>
                <span class="ml-2 shrink-0 text-xs text-slate-500">{{ item.template_type }}</span>
              </button>
              <div v-if="templateList.length === 0" class="px-3 py-3 text-sm text-slate-400">暂无模板，请先上传</div>
            </div>
          </div>
        </div>

        <!-- Tab 切换 -->
        <div class="flex border-b bg-white">
          <button
            v-for="tab in [{id:'fields',label:'字段选择'},{id:'excel',label:'Excel 列映射'},{id:'word',label:'Word/PDF 占位符'}]"
            :key="tab.id"
            type="button"
            class="px-5 py-2.5 text-sm font-medium border-b-2 transition-colors"
            :class="exportConfigTab === tab.id
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'"
            @click="exportConfigTab = tab.id"
          >
            {{ tab.label }}
            <span v-if="tab.id === 'excel'" class="ml-1 rounded-full bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
              {{ mappingForm.config.excel_columns?.length ?? 0 }}
            </span>
            <span v-if="tab.id === 'word'" class="ml-1 rounded-full bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
              {{ mappingForm.config.word_placeholders?.length ?? 0 }}
            </span>
          </button>
        </div>

        <!-- Tab 内容区 -->
        <div class="flex-1 overflow-y-auto">

          <!-- ===== Tab 1: 字段选择 ===== -->
          <div v-show="exportConfigTab === 'fields'" class="flex h-full flex-col">
            <!-- 工具栏 -->
            <div class="flex flex-wrap items-center gap-2 border-b bg-slate-50 px-4 py-2">
              <input v-model.trim="fieldKeyword" type="text" class="w-44 rounded border px-2 py-1.5 text-sm" placeholder="搜索字段名称/编码…" />
              <label class="flex items-center gap-1.5 text-xs text-slate-600">
                <input v-model="showAdvancedFields" type="checkbox" />
                显示全部字段（含导入/评审/仲裁）
              </label>
              <label class="flex items-center gap-1.5 text-xs text-slate-600">
                <input v-model="presetForm.include_base" type="checkbox" />
                包含基础信息
              </label>
              <button type="button" class="rounded border border-slate-300 px-2 py-1.5 text-xs text-slate-700 hover:bg-white" @click="applyBuiltInLongFormPreset">一键生成常用占位符</button>
            </div>

            <!-- 树形区域 -->
            <div class="flex-1 overflow-y-auto">
              <!-- 综合汇总字段（submission 分组：总分、排名等） -->
              <div v-if="summaryFields.length > 0" class="border-b border-slate-200">
                <div class="flex items-center justify-between bg-slate-600 px-4 py-2.5 text-white">
                  <span class="text-sm font-semibold">综合汇总</span>
                  <span class="text-xs text-white/60">{{ summaryFields.length }} 个字段</span>
                </div>
                <div class="divide-y divide-slate-100">
                  <div
                    v-for="f in summaryFields"
                    :key="f.key"
                    class="flex cursor-pointer items-center justify-between px-4 py-1.5 hover:bg-slate-100"
                    :class="selectedFieldKeys.has(f.key) ? 'bg-brand-50' : ''"
                    @click="onTreeToggleField(f.key)"
                  >
                    <div class="flex items-center gap-2">
                      <input
                        type="checkbox"
                        class="h-3.5 w-3.5 cursor-pointer rounded"
                        :checked="selectedFieldKeys.has(f.key)"
                        @click.stop
                        @change="onTreeToggleField(f.key)"
                      />
                      <span class="rounded bg-brand-100 px-1 text-xs text-brand-700">汇总</span>
                      <span class="text-sm text-slate-700">{{ f.label }}</span>
                      <span
                        v-if="FIELD_TOOLTIPS[f.split_type] || FIELD_TOOLTIPS[f.key]"
                        class="shrink-0 cursor-help select-none text-slate-400 hover:text-slate-600"
                        :title="FIELD_TOOLTIPS[f.split_type] || FIELD_TOOLTIPS[f.key]"
                      >ⓘ</span>
                    </div>
                    <code class="ml-2 shrink-0 select-all rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-500">{{ f.key }}</code>
                  </div>
                </div>
              </div>

              <ExportFieldTreeNode
                v-for="rootNode in filteredFieldTree"
                :key="rootNode.id"
                :node="rootNode"
                :depth="0"
                :selected-keys="selectedFieldKeys"
                @toggle-field="onTreeToggleField"
                @add-common="addAllNodeCommonFields"
              />
              <p v-if="filteredFieldTree.length === 0" class="py-8 text-center text-sm text-slate-400">暂无匹配字段，请先选择项目或检查搜索关键字</p>
            </div>

            <!-- 批量操作 sticky 底部 -->
            <div class="sticky bottom-0 flex items-center justify-between border-t bg-white px-4 py-2.5">
              <div class="flex items-center gap-2 text-sm text-slate-600">
                <span class="font-medium text-brand-700">已选 {{ selectedFieldKeys.size }} 个字段</span>
                <button v-if="selectedFieldKeys.size > 0" type="button" class="text-xs text-slate-400 hover:text-slate-600" @click="clearFieldSelection">清空选择</button>
              </div>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="rounded border border-brand-500 px-3 py-1.5 text-xs font-medium text-brand-700 hover:bg-brand-50 disabled:opacity-40"
                  :disabled="selectedFieldKeys.size === 0"
                  @click="batchAddToWordPlaceholders"
                >批量加入 Word 占位符</button>
                <button
                  type="button"
                  class="rounded border border-slate-400 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                  :disabled="selectedFieldKeys.size === 0"
                  @click="batchAddToExcelColumns"
                >批量加入 Excel 列</button>
              </div>
            </div>
          </div>

          <!-- ===== Tab 2: Excel 列映射 ===== -->
          <div v-show="exportConfigTab === 'excel'" class="p-4">
            <div class="mb-3 flex items-center justify-between">
              <span class="text-sm font-medium text-slate-700">Excel 列映射</span>
              <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="addExcelColumnMapping">+ 新增列</button>
            </div>
            <!-- 行号与表头写入配置 -->
            <div class="mb-4 rounded border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
              <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
                <label class="flex items-center gap-2">
                  <span class="shrink-0 text-xs font-medium text-slate-600">数据写入起始行：</span>
                  <input
                    v-model.number="mappingForm.config.data_start_row"
                    type="number"
                    min="1"
                    class="w-16 rounded border border-slate-300 bg-white px-2 py-1 text-center text-sm font-mono focus:border-brand-500 focus:outline-none"
                  />
                  <span class="text-xs text-slate-400">（使用带合并标题的模板时，填入模板第一个数据行的行号，如第 8 行）</span>
                </label>
                <label class="flex cursor-pointer items-center gap-2">
                  <input v-model="mappingForm.config.write_header" type="checkbox" class="cursor-pointer" />
                  <span class="text-xs text-slate-700">写入表头行</span>
                  <span class="text-xs text-slate-400">（使用模板时通常不勾选，以保留模板中的合并标题行）</span>
                </label>
              </div>
            </div>
            <!-- 静态单元格：共享元数据一次性写入指定单元格 -->
            <div class="mb-4 rounded border border-slate-200 bg-slate-50 px-4 py-3">
              <div class="mb-2 flex items-center justify-between">
                <div>
                  <span class="text-xs font-medium text-slate-700">静态单元格（写一次的共享信息）</span>
                  <span class="ml-2 text-xs text-slate-400">如专业、年级、参评人数——只填入一次，不随学生数据循环重复</span>
                </div>
                <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="addStaticCellMapping">+ 新增</button>
              </div>
              <div class="space-y-2">
                <div
                  v-for="(sc, idx) in mappingForm.config.static_cells"
                  :key="`sc-${idx}`"
                  class="grid grid-cols-12 items-center gap-2"
                >
                  <input
                    v-model.trim="sc.cell"
                    type="text"
                    class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-center text-sm font-mono focus:border-brand-500 focus:outline-none"
                    placeholder="C3"
                  />
                  <select
                    v-model="sc.field_key"
                    :disabled="sc.aggregation === 'count'"
                    class="col-span-7 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm disabled:opacity-50"
                  >
                    <option value="">请选择字段</option>
                    <option value="_count">参评人数（行数统计）</option>
                    <optgroup v-for="group in groupedDisplayFields" :key="`sc-${group.id}`" :label="group.label">
                      <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
                    </optgroup>
                  </select>
                  <select
                    v-model="sc.aggregation"
                    class="col-span-2 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
                  >
                    <option value="first">取第一行值</option>
                    <option value="count">行数统计</option>
                  </select>
                  <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="removeStaticCellMapping(idx)">删除</button>
                </div>
                <p v-if="!mappingForm.config.static_cells?.length" class="py-3 text-center text-xs text-slate-400">暂无静态单元格配置，点击"新增"添加（如：C3 → 专业名）</p>
              </div>
            </div>
            <div class="space-y-2">
              <div v-for="(row, idx) in mappingForm.config.excel_columns" :key="`excel-${idx}`" class="grid grid-cols-12 items-center gap-2">
                <input v-model.trim="row.column" type="text" class="col-span-1 rounded border px-2 py-1.5 text-center text-sm font-mono" placeholder="A" />
                <select v-model="row.field_key" class="col-span-8 rounded border px-2 py-1.5 text-sm">
                  <option value="">请选择字段</option>
                  <optgroup v-for="group in groupedDisplayFields" :key="`excel-${group.id}`" :label="group.label">
                    <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
                  </optgroup>
                </select>
                <input v-model.trim="row.header" type="text" class="col-span-2 rounded border px-2 py-1.5 text-sm" placeholder="表头" />
                <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="removeExcelColumnMapping(idx)">删除</button>
              </div>
              <p v-if="!mappingForm.config.excel_columns?.length" class="py-6 text-center text-sm text-slate-400">暂无列配置，点击"新增列"或从字段选择 Tab 批量加入</p>
            </div>
          </div>

          <!-- ===== Tab 3: Word/PDF 占位符映射 ===== -->
          <div v-show="exportConfigTab === 'word'" class="p-4">
            <div class="mb-3 flex items-center justify-between">
              <span class="text-sm font-medium text-slate-700">Word/PDF 占位符映射</span>
              <button type="button" class="rounded border border-brand-500 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50" @click="addWordPlaceholderMapping">+ 新增占位符</button>
            </div>
            <p class="mb-3 text-xs text-slate-500">在 Word 模板中直接写 <code class="rounded bg-slate-100 px-1">@占位符名称</code>（如 @student_no、@A1-self），此处配置占位符对应的数据字段。</p>
            <div class="space-y-2">
              <div v-for="(row, idx) in mappingForm.config.word_placeholders" :key="`word-${idx}`" class="rounded border bg-slate-50/50 p-2">
                <div class="grid grid-cols-12 items-center gap-2">
                  <div class="col-span-1 text-center text-xs text-slate-400">@</div>
                  <input v-model.trim="row.placeholder" type="text" class="col-span-4 rounded border bg-white px-2 py-1.5 text-sm font-mono" placeholder="占位符名称" />
                  <select v-model="row.field_key" class="col-span-6 rounded border bg-white px-2 py-1.5 text-sm">
                    <option value="">请选择对应字段</option>
                    <optgroup v-for="group in groupedDisplayFields" :key="`word-${group.id}`" :label="group.label">
                      <option v-for="field in group.fields" :key="field.key" :value="field.key">{{ field.label }} ({{ field.key }})</option>
                    </optgroup>
                  </select>
                  <button type="button" class="col-span-1 text-center text-xs text-red-500 hover:text-red-700" @click="removeWordPlaceholderMapping(idx)">删除</button>
                </div>
                <div class="mt-1 flex items-center justify-between px-1 text-xs text-slate-400">
                  <span>模板写法：<code class="rounded bg-slate-200 px-1 font-mono">{{ formatTokenPreview(row.placeholder) }}</code></span>
                  <span class="truncate px-2">{{ getFieldDisplayName(row.field_key) }}</span>
                  <button type="button" class="text-brand-600 hover:text-brand-800" @click="copyTokenPreview(row.placeholder)">复制</button>
                </div>
              </div>
              <p v-if="!mappingForm.config.word_placeholders?.length" class="py-6 text-center text-sm text-slate-400">暂无占位符配置，点击"新增占位符"或从字段选择 Tab 批量加入</p>
            </div>
            <!-- ZIP 文件名模板配置 -->
            <div v-if="mappingForm.output_format !== 'xlsx'" class="mt-4 rounded border border-dashed border-slate-300 bg-slate-50 p-3">
              <label class="mb-1 block text-xs font-medium text-slate-600">ZIP 内文件名模板（多文件导出时生效）</label>
              <input
                v-model="mappingForm.config.zip_filename_pattern"
                type="text"
                class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm font-mono"
                placeholder="{student_no}_{real_name}"
              />
              <p class="mt-1 text-xs text-slate-400">可用变量：{student_no} {real_name} {class_name} {department} {rank} {username}。留空则默认使用 {real_name}。</p>
            </div>
          </div>

        </div>

        <!-- 底部操作栏 -->
        <div class="sticky bottom-0 flex flex-wrap items-center justify-between gap-3 border-t bg-white px-5 py-3">
          <div class="flex flex-wrap items-center gap-3">
            <button type="button" class="rounded border border-brand-500 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50" :disabled="savingMapping" @click="saveMapping">
              {{ savingMapping ? '保存中…' : '保存映射' }}
            </button>
            <label v-if="mappingForm.output_format !== 'xlsx'" class="flex cursor-pointer items-center gap-1.5 text-xs text-slate-600">
              <input v-model="pageExportMultiFile" type="checkbox" class="cursor-pointer" />
              每人单独文件（ZIP）
            </label>
            <select v-if="mappingForm.output_format !== 'xlsx' && pageExportMultiFile"
                    v-model="pageExportGroupBy"
                    class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">
              <option value="">不分组（平铺）</option>
              <option value="class">按班级子目录</option>
            </select>
            <button type="button" class="rounded border border-green-600 px-3 py-1.5 text-sm text-green-700 hover:bg-green-50" :disabled="exporting" @click="doConfiguredExport">
              使用该配置导出
            </button>
          </div>
          <p v-if="configError" class="text-sm text-red-600">{{ configError }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
/**
 * 成绩报表页：
 * - 学生：展示本人各项目最终得分与得分明细（GET /report/student/me/）。
 * - 主任/管理员：选择项目后查看班级汇总（summary）与总分排名（ranking），并可导出 Excel/PDF。
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getSeasons, getSeasonProjects } from '@/api/eval'
import {
  getMyReport,
  getProjectSummary,
  getProjectRanking,
  exportReport,
  getExportFields,
  getExportTemplates,
  createExportTemplate,
  getExportMappings,
  createExportMapping,
  updateExportMapping,
  getDepartments,
  getMajors,
  getClasses,
} from '@/api/report'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'
import { deriveSubmissionDisplayStatus } from '@/utils/submissionStatus'
import ExportFieldTreeNode from './ExportFieldTreeNode.vue'

const auth = useAuthStore()
const router = useRouter()

/** 当前角色等级：-1=未登录，0=学生，1=学生助理，2=评审老师，3=院系主任，5=超级管理员 */
const currentLevel = computed(() => auth.user?.current_role?.level ?? -1)
const isStudent = computed(() => {
  if (currentLevel.value >= 2) return false
  if (currentLevel.value === 1) {
    const scopeType = auth.user?.current_role?.scope_type
    return scopeType !== 'class' && scopeType !== 'department'
  }
  return currentLevel.value <= 0
})
/** 评审老师（level=2）或有班级/院系管理权限的学生助理（level=1），仅可看负责班级数据 */
const isCounselor = computed(() => {
  if (currentLevel.value === 2) return true
  if (currentLevel.value === 1) {
    const scopeType = auth.user?.current_role?.scope_type
    return scopeType === 'class' || scopeType === 'department'
  }
  return false
})
/** 主任及以上（level>=3）可看全项目报表 */
const isDirectorOrAdmin = computed(() => currentLevel.value >= 3)

// ====== 学生视图 ======
const myLoading = ref(false)
const myError = ref('')
const myReport = ref([])

async function loadMyReport() {
  myLoading.value = true
  myError.value = ''
  try {
    myReport.value = await getMyReport()
  } catch (e) {
    myError.value = e.response?.data?.detail ?? '加载成绩失败'
    myReport.value = []
  } finally {
    myLoading.value = false
  }
}

// ====== 管理/主任视图 ======
const seasons = ref([])
const projects = ref([])
const selectedSeasonId = ref('')
const selectedProjectId = ref('')

/**
 * 状态排序优先级：进行中 > 草稿 > 已结束/其他
 * @param {string} status
 * @returns {number}
 */
function statusOrder(status) {
  if (status === 'ongoing') return 0
  if (status === 'draft') return 1
  return 2
}

/** 周期列表按状态优先级排序：进行中在前 */
const sortedSeasons = computed(() =>
  [...seasons.value].sort((a, b) => statusOrder(a.status) - statusOrder(b.status))
)

/** 项目列表按状态优先级排序：进行中在前 */
const sortedProjects = computed(() =>
  [...projects.value].sort((a, b) => statusOrder(a.status) - statusOrder(b.status))
)

/** 汇总数据 */
const summary = ref(null)
/** 排名数据 */
const ranking = ref(null)
const rankingPage = ref(1)
const rankingPageSize = 20
const reportLoading = ref(false)
const rankingPaginating = ref(false)
const reportError = ref('')

/** 导出状态 */
const exporting = ref(false)
const exportError = ref('')
const exportConfigVisible = ref(false)
const configError = ref('')
const exportFields = ref([])
const allExportFields = ref([])
const fieldGroups = ref([])
const fieldTree = ref([])

// Tooltip descriptions for each field split_type, shown on hover in the field tree
const FIELD_TOOLTIPS = {
  self_score: '学生本人填写的原始自评分',
  process_record: '学生自评时填写的过程说明文字',
  reviewer_score: '评审老师打出的分数（如启用双评，按项目规则取均值/最大值/第一次）',
  arbitration_score: '当双评分差超出阈值时由仲裁员最终确定的分，可覆盖评审分',
  final_adopted_score: '最终确认分：优先取仲裁分，否则按规则合并多轮评审分（这就是最终成绩）',
  imported_score: '通过 Excel 批量导入的外部成绩（如体测成绩、课程成绩）',
  agg_score: '该模块所有子指标的加权汇总总分',
  evidence_count: '学生上传的佐证材料数量',
  evidence_names: '佐证材料文件名列表（分号分隔）',
  evidence_urls: '佐证材料下载链接列表（换行分隔）',
  final_score: '综合总分：所有一级模块（F1/F2...）按权重加权求和后的最终成绩',
  rank: '该学生在本次测评中的综合排名（按总分降序）',
}
const exportPresets = ref([])
const selectedFieldCategory = ref('')
const fieldKeyword = ref('')
const showAdvancedFields = ref(false)
const fieldViewMode = ref('template_common_first')
const expandedModules = ref({})
const expandedIndicators = ref({})
const presetForm = ref({
  include_base: true,
  modules: [],
})
/** 导出配置弹窗 Tab */
const exportConfigTab = ref('fields')
/** 模板管理面板展开状态 */
const templatePanelOpen = ref(false)
/** 字段多选状态 */
const selectedFieldKeys = ref(new Set())
const templateList = ref([])
const mappingList = ref([])
const selectedTemplateId = ref(null)
const selectedMappingId = ref(null)
const uploadingTemplate = ref(false)
const savingMapping = ref(false)
const templateForm = ref({
  name: '',
  template_type: 'word',
  visibility: 'private',
  file: null,
})
const mappingForm = ref({
  name: '',
  output_format: 'xlsx',
  is_default: false,
  config: {
    token_mode: 'prefix_token',
    token_prefix: '@',
    field_version: 2,
    field_view_mode: 'template_common_first',
    common_profile_version: 1,
    header_row: 1,
    data_start_row: 2,
    write_header: true,
    static_cells: [],
    excel_columns: [
      { column: 'A', field_key: 'rank', header: '排名' },
      { column: 'B', field_key: 'student_no', header: '学号' },
      { column: 'C', field_key: 'real_name', header: '姓名' },
      { column: 'D', field_key: 'class_name', header: '班级' },
      { column: 'E', field_key: 'final_score', header: '总分' },
    ],
    word_placeholders: [],
    zip_filename_pattern: '',
  },
})
const totalPages = computed(() =>
  ranking.value ? Math.ceil(ranking.value.total / rankingPageSize) : 1
)

/** 当前选中项目名称 */
const selectedProjectName = computed(() => {
  const p = projects.value.find((p) => p.id === selectedProjectId.value)
  return p?.name ?? ''
})

/** 报表筛选条件（看到什么导出什么） */
const reportFilters = ref({
  department_id: '',
  major_id: '',
  class_id: '',
  search: '',
})
const departmentOptions = ref([])
const majorOptions = ref([])
const classOptions = ref([])

/** 主页面导出设置 */
const pageExportFormat = ref('xlsx')
const pageExportMappingId = ref(null)
const pageExportMultiFile = ref(false)
const pageExportGroupBy = ref('')  // '' = 不分组, 'class' = 按班级子目录

/**
 * @description 当前筛选参数（空值自动剔除）。
 * @returns {Object}
 */
function getFilterParams() {
  const params = {}
  if (reportFilters.value.department_id) params.department_id = reportFilters.value.department_id
  if (reportFilters.value.major_id) params.major_id = reportFilters.value.major_id
  if (reportFilters.value.class_id) params.class_id = reportFilters.value.class_id
  if (String(reportFilters.value.search || '').trim()) params.search = String(reportFilters.value.search).trim()
  return params
}

/**
 * @description 根据当前输出格式筛选可用映射。
 * @returns {Array}
 */
const pageExportMappingCandidates = computed(() => {
  const fmt = pageExportFormat.value
  return (mappingList.value || []).filter((item) => {
    if (fmt === 'xlsx') return item.output_format === 'xlsx'
    return item.output_format === 'word' || item.output_format === 'pdf'
  })
})

/**
 * 根据分类和关键字过滤字段，并按分组输出。
 */
const groupedFilteredFields = computed(() => {
  const keyword = fieldKeyword.value.trim().toLowerCase()
  const category = selectedFieldCategory.value
  const sourceFields = showAdvancedFields.value ? allExportFields.value : exportFields.value
  const groupsMap = new Map((fieldGroups.value || []).map((g) => [g.id, { ...g, fields: [] }]))
  for (const field of sourceFields || []) {
    if (category && field.category_id !== category) continue
    if (keyword) {
      const hit = String(field.label || '').toLowerCase().includes(keyword) || String(field.key || '').toLowerCase().includes(keyword)
      if (!hit) continue
    }
    const gid = field.category_id || 'other'
    if (!groupsMap.has(gid)) groupsMap.set(gid, { id: gid, label: field.category_label || gid, order: 999, fields: [] })
    groupsMap.get(gid).fields.push(field)
  }
  const groups = Array.from(groupsMap.values())
    .filter((g) => g.fields.length > 0)
    .sort((a, b) => (a.order ?? 999) - (b.order ?? 999))
  groups.forEach((g) => {
    g.fields.sort((a, b) => {
      if (g.id === 'indicators') {
        const am = Number(a.module_order ?? 999)
        const bm = Number(b.module_order ?? 999)
        if (am !== bm) return am - bm
        const ai = Number(a.indicator_order ?? 999999)
        const bi = Number(b.indicator_order ?? 999999)
        if (ai !== bi) return ai - bi
        const at = Number(a.field_type_order ?? 999)
        const bt = Number(b.field_type_order ?? 999)
        if (at !== bt) return at - bt
      }
      const ao = Number(a.order ?? 999999)
      const bo = Number(b.order ?? 999999)
      if (ao !== bo) return ao - bo
      return String(a.label || '').localeCompare(String(b.label || ''), 'zh-CN')
    })
  })
  return groups
})

const groupedDisplayFields = computed(() => groupedFilteredFields.value)

/**
 * Submission-level summary fields (final_score, rank, etc.) from allExportFields.
 * Filtered by fieldKeyword so search works on them too.
 */
const summaryFields = computed(() => {
  const keyword = fieldKeyword.value.trim().toLowerCase()
  return (allExportFields.value || []).filter((f) => {
    if (f.category_id !== 'submission') return false
    if (f.key === 'submission_id') return false
    if (!keyword) return true
    return (
      String(f.label || '').toLowerCase().includes(keyword) ||
      String(f.key || '').toLowerCase().includes(keyword)
    )
  })
})

/**
 * Dynamic list of modules derived from the actual field tree — no hardcoding.
 * Each entry: { key, label, code } e.g. { key: 'F', label: '德育评分', code: 'F1' }
 */
const availableModules = computed(() =>
  (fieldTree.value || []).map((m) => ({
    key: m.category || String(m.id),
    label: m.name,
    code: m.category || '',
  }))
)

const filteredFieldTree = computed(() => {
  const keyword = fieldKeyword.value.trim().toLowerCase()

  // Recursively filter a node: keep only branches that have matching fields
  function filterNode(node) {
    // Filter direct fields of this node
    const matchedFields = (node.fields || []).filter((f) => {
      if (!keyword) return true
      return (
        String(f.label || '').toLowerCase().includes(keyword) ||
        String(f.key || '').toLowerCase().includes(keyword)
      )
    })

    // Recursively filter children
    const filteredChildren = (node.children || []).map(filterNode).filter(Boolean)

    // Keep this node if it has any matching direct fields or surviving children
    if (matchedFields.length === 0 && filteredChildren.length === 0 && keyword) {
      return null
    }

    return {
      ...node,
      fields: matchedFields,
      children: filteredChildren,
    }
  }

  return (fieldTree.value || []).map(filterNode).filter(Boolean)
})

/**
 * 加载测评周期列表，并自动选中「进行中」的周期（若有）。
 * 选中后自动触发项目加载及默认选中。
 */
async function loadSeasons() {
  try {
    seasons.value = await getSeasons()
    if (seasons.value.length > 0 && !selectedSeasonId.value) {
      const ongoing = seasons.value.find((s) => s.status === 'ongoing')
      const autoSeason = ongoing ?? seasons.value[0]
      selectedSeasonId.value = autoSeason.id
      await autoLoadProjects(autoSeason.id)
    }
  } catch {
    seasons.value = []
  }
}

/**
 * @description 加载筛选下拉：院系。
 * @returns {Promise<void>}
 */
async function loadDepartmentOptions() {
  try {
    departmentOptions.value = await getDepartments()
  } catch {
    departmentOptions.value = []
  }
}

/**
 * @description 加载筛选下拉：专业。
 * @returns {Promise<void>}
 */
async function loadMajorOptions() {
  const params = {}
  if (reportFilters.value.department_id) params.department = reportFilters.value.department_id
  try {
    majorOptions.value = await getMajors(params)
  } catch {
    majorOptions.value = []
  }
}

/**
 * @description 加载筛选下拉：班级。
 * @returns {Promise<void>}
 */
async function loadClassOptions() {
  const params = {}
  if (reportFilters.value.department_id) params.department = reportFilters.value.department_id
  if (reportFilters.value.major_id) params.major = reportFilters.value.major_id
  try {
    classOptions.value = await getClasses(params)
  } catch {
    classOptions.value = []
  }
}

/**
 * 加载指定周期的项目列表，并自动选中优先级最高的项目。
 * 优先级：进行中 > 草稿 > 已结束 > 列表第一个。
 * @param {number} seasonId
 */
async function autoLoadProjects(seasonId) {
  try {
    projects.value = await getSeasonProjects(seasonId)
    if (projects.value.length > 0) {
      const ongoingProject = projects.value.find((p) => p.status === 'ongoing')
      const draftProject = projects.value.find((p) => p.status === 'draft')
      const autoProject = ongoingProject ?? draftProject ?? projects.value[0]
      selectedProjectId.value = autoProject.id
      await refreshTemplateAndMappings()
      await loadProjectReport()
    }
  } catch {
    projects.value = []
  }
}

async function onSeasonChange() {
  selectedProjectId.value = ''
  projects.value = []
  summary.value = null
  ranking.value = null
  await refreshTemplateAndMappings()
  if (!selectedSeasonId.value) return
  await autoLoadProjects(selectedSeasonId.value)
}

async function onProjectChange() {
  summary.value = null
  ranking.value = null
  rankingPage.value = 1
  if (!selectedProjectId.value) return
  await refreshTemplateAndMappings()
  await loadProjectReport()
}

/**
 * @description 院系筛选变化后联动刷新专业/班级。
 * @returns {Promise<void>}
 */
async function onDepartmentFilterChange() {
  reportFilters.value.major_id = ''
  reportFilters.value.class_id = ''
  await Promise.all([loadMajorOptions(), loadClassOptions()])
}

/**
 * @description 专业筛选变化后联动刷新班级。
 * @returns {Promise<void>}
 */
async function onMajorFilterChange() {
  reportFilters.value.class_id = ''
  await loadClassOptions()
}

/**
 * @description 应用筛选并刷新汇总/排名。
 * @returns {Promise<void>}
 */
async function applyReportFilters() {
  rankingPage.value = 1
  if (!selectedProjectId.value) return
  await loadProjectReport()
}

/**
 * @description 重置筛选并刷新汇总/排名。
 * @returns {Promise<void>}
 */
async function resetReportFilters() {
  reportFilters.value.department_id = ''
  reportFilters.value.major_id = ''
  reportFilters.value.class_id = ''
  reportFilters.value.search = ''
  await Promise.all([loadMajorOptions(), loadClassOptions()])
  await applyReportFilters()
}

async function loadProjectReport() {
  reportLoading.value = true
  reportError.value = ''
  try {
    const filterParams = getFilterParams()
    const [s, r] = await Promise.all([
      getProjectSummary(selectedProjectId.value, filterParams),
      getProjectRanking(selectedProjectId.value, rankingPage.value, rankingPageSize, filterParams),
    ])
    summary.value = s
    ranking.value = r
  } catch (e) {
    reportError.value = e.response?.data?.detail ?? '加载报表失败'
  } finally {
    reportLoading.value = false
  }
}

async function gotoRankingPage(page) {
  rankingPage.value = page
  rankingPaginating.value = true
  try {
    ranking.value = await getProjectRanking(selectedProjectId.value, page, rankingPageSize, getFilterParams())
  } catch (e) {
    reportError.value = e.response?.data?.detail ?? '加载排名失败'
  } finally {
    rankingPaginating.value = false
  }
}

/**
 * 打开导出模板配置面板并加载基础数据。
 * @returns {Promise<void>}
 */
async function refreshTemplateAndMappings() {
  if (!selectedProjectId.value) {
    templateList.value = []
    mappingList.value = []
    selectedTemplateId.value = null
    selectedMappingId.value = null
    pageExportMappingId.value = null
    return
  }
  const [templates, mappings] = await Promise.all([
    getExportTemplates({ project_id: selectedProjectId.value }),
    getExportMappings({ project_id: selectedProjectId.value }),
  ])
  templateList.value = templates || []
  mappingList.value = mappings || []

  const templateExists = templateList.value.some((item) => item.id === selectedTemplateId.value)
  if (!templateExists) {
    selectedTemplateId.value = null
  }
  if (!selectedTemplateId.value && templateList.value.length) {
    selectedTemplateId.value = templateList.value[0].id
  }

  const mappingExists = mappingList.value.some((item) => item.id === selectedMappingId.value)
  if (!mappingExists) {
    selectedMappingId.value = null
  }
  if (!selectedMappingId.value && mappingList.value.length) {
    const prefer = mappingList.value.find((x) => x.is_default) || mappingList.value[0]
    selectedMappingId.value = prefer.id
  }

  const pageMappingExists = pageExportMappingCandidates.value.some((item) => item.id === pageExportMappingId.value)
  if (!pageMappingExists) {
    pageExportMappingId.value = null
  }
  if (!pageExportMappingId.value && pageExportMappingCandidates.value.length) {
    const preferPage = pageExportMappingCandidates.value.find((x) => x.is_default) || pageExportMappingCandidates.value[0]
    pageExportMappingId.value = preferPage.id
  }
  onPageExportFormatChange()
}

async function openExportConfig() {
  if (!selectedProjectId.value) return
  exportConfigVisible.value = true
  exportConfigTab.value = 'fields'
  selectedFieldKeys.value = new Set()
  expandedModules.value = {}
  expandedIndicators.value = {}
  configError.value = ''
  try {
    const [fieldResp] = await Promise.all([
      getExportFields(selectedProjectId.value, { view_mode: fieldViewMode.value }),
      refreshTemplateAndMappings(),
    ])
    exportFields.value = fieldResp.fields || []
    allExportFields.value = fieldResp.all_fields || fieldResp.fields || []
    fieldGroups.value = fieldResp.field_groups || []
    fieldTree.value = fieldResp.field_tree || []
    exportPresets.value = fieldResp.presets || []
    applyTreeFallbackFromFlat()
    ensureTreeExpanded()
    fieldViewMode.value = fieldResp.field_view_mode || fieldViewMode.value
    // Auto-populate preset module selection from actual tree modules
    presetForm.value.modules = (fieldTree.value || []).map((m) => m.category || String(m.id))
    if (mappingList.value.length) {
      const prefer = mappingList.value.find((x) => x.id === selectedMappingId.value)
        || mappingList.value.find((x) => x.is_default)
        || mappingList.value[0]
      selectedMappingId.value = prefer?.id ?? null
      mappingForm.value.name = prefer.name
      mappingForm.value.output_format = prefer.output_format
      mappingForm.value.is_default = !!prefer.is_default
      mappingForm.value.config = normalizeMappingConfig(prefer.config)
      if (prefer.template) {
        const templateExists = (templateList.value || []).some((t) => t.id === prefer.template)
        if (templateExists) {
          selectedTemplateId.value = prefer.template
        } else {
          selectedTemplateId.value = null
          configError.value = '当前映射关联的模板已失效，请重新选择模板并保存映射'
        }
      }
    }
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '加载导出配置失败'
  }
}

/**
 * 关闭导出模板配置面板。
 * @returns {void}
 */
function closeExportConfig() {
  exportConfigVisible.value = false
}

/**
 * 标准化映射配置，确保必要数组字段始终存在。
 * @param {Object} cfg
 * @returns {Object}
 */
function normalizeMappingConfig(cfg = {}) {
  const defaultColumns = [
    { column: 'A', field_key: 'rank', header: '排名' },
    { column: 'B', field_key: 'student_no', header: '学号' },
    { column: 'C', field_key: 'real_name', header: '姓名' },
    { column: 'D', field_key: 'class_name', header: '班级' },
    { column: 'E', field_key: 'final_score', header: '总分' },
  ]
  return {
    token_mode: cfg.token_mode ?? 'prefix_token',
    token_prefix: cfg.token_prefix ?? '@',
    field_version: cfg.field_version ?? 2,
    field_view_mode: cfg.field_view_mode ?? 'template_common_first',
    common_profile_version: cfg.common_profile_version ?? 1,
    header_row: cfg.header_row ?? 1,
    data_start_row: cfg.data_start_row ?? 2,
    write_header: cfg.write_header !== undefined ? cfg.write_header : true,
    static_cells: Array.isArray(cfg.static_cells) ? cfg.static_cells : [],
    excel_columns: Array.isArray(cfg.excel_columns) && cfg.excel_columns.length ? cfg.excel_columns : defaultColumns,
    word_placeholders: Array.isArray(cfg.word_placeholders) ? cfg.word_placeholders : [],
    zip_filename_pattern: cfg.zip_filename_pattern ?? '',
  }
}

/**
 * 处理模板文件选择。
 * @param {Event} e
 * @returns {void}
 */
function onTemplateFileChange(e) {
  const file = e.target?.files?.[0]
  templateForm.value.file = file || null
}

/**
 * 上传导出模板。
 * @returns {Promise<void>}
 */
async function uploadTemplate() {
  configError.value = ''
  if (!selectedProjectId.value) return
  if (!templateForm.value.name || !templateForm.value.file) {
    configError.value = '请填写模板名称并选择文件'
    return
  }
  uploadingTemplate.value = true
  try {
    const fd = new FormData()
    fd.append('name', templateForm.value.name)
    fd.append('template_type', templateForm.value.template_type)
    fd.append('visibility', templateForm.value.visibility)
    fd.append('project', selectedProjectId.value)
    fd.append('file', templateForm.value.file)
    const created = await createExportTemplate(fd)
    templateList.value.unshift(created)
    selectedTemplateId.value = created.id
    // #endregion
    templateForm.value.name = ''
    templateForm.value.file = null
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '模板上传失败'
  } finally {
    uploadingTemplate.value = false
  }
}

/**
 * 新增 Excel 列映射行。
 * @returns {void}
 */
function addExcelColumnMapping() {
  mappingForm.value.config.excel_columns.push({ column: '', field_key: '', header: '' })
}

/**
 * 新增静态单元格映射行。
 * @returns {void}
 */
function addStaticCellMapping() {
  mappingForm.value.config.static_cells.push({ cell: '', field_key: '', aggregation: 'first' })
}

/**
 * 删除静态单元格映射行。
 * @param {number} idx
 * @returns {void}
 */
function removeStaticCellMapping(idx) {
  mappingForm.value.config.static_cells.splice(idx, 1)
}

/**
 * 删除 Excel 列映射行。
 * @param {number} idx
 * @returns {void}
 */
function removeExcelColumnMapping(idx) {
  mappingForm.value.config.excel_columns.splice(idx, 1)
}

/**
 * 新增 Word 占位符映射行。
 * @returns {void}
 */
function addWordPlaceholderMapping() {
  mappingForm.value.config.word_placeholders.push({ placeholder: '', field_key: '' })
}

/**
 * 删除 Word 占位符映射行。
 * @param {number} idx
 * @returns {void}
 */
function removeWordPlaceholderMapping(idx) {
  mappingForm.value.config.word_placeholders.splice(idx, 1)
}

/**
 * 规范化占位符预览文本，默认 @ 前缀。
 * @param {string} raw
 * @returns {string}
 */
function formatTokenPreview(raw) {
  const prefix = mappingForm.value.config.token_prefix || '@'
  const token = String(raw || '').trim()
  if (!token) return `${prefix}token`
  return token.startsWith(prefix) ? token : `${prefix}${token}`
}

/**
 * 复制占位符预览。
 * @param {string} raw
 * @returns {Promise<void>}
 */
async function copyTokenPreview(raw) {
  const text = formatTokenPreview(raw)
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // 低权限浏览器兜底：提示用户手动复制
    configError.value = `复制失败，请手动复制：${text}`
  }
}

/**
 * 按指标一键加入“自评分/过程记录/最终分”常用占位符映射。
 * 仅补全缺失项，不覆盖已配置项。
 * @returns {void}
 */
function quickAddIndicatorCommonPlaceholders() {
  const rows = mappingForm.value.config.word_placeholders || []
  const exists = new Set(rows.map((r) => `${(r.placeholder || '').trim()}|${r.field_key || ''}`))
  const indicatorCommon = (allExportFields.value || []).filter((f) => {
    if (f.category_id !== 'indicators' || !f.is_common) return false
    const moduleKey = String(f.module_key || '').toUpperCase()
    return presetForm.value.modules.includes(moduleKey)
  })
  const baseCommon = presetForm.value.include_base
    ? (allExportFields.value || []).filter((f) => f.category_id !== 'indicators' && f.is_common)
    : []
  const merged = [...baseCommon, ...indicatorCommon]
  for (const field of merged) {
    const token = field.key
    const key = `${token}|${field.key}`
    if (exists.has(key)) continue
    rows.push({ placeholder: token, field_key: field.key })
    exists.add(key)
  }
  mappingForm.value.config.word_placeholders = rows
}

function toggleModule(moduleKey) {
  const next = { ...(expandedModules.value || {}) }
  next[moduleKey] = !next[moduleKey]
  expandedModules.value = next
}

function toggleIndicator(indicatorKey) {
  const next = { ...(expandedIndicators.value || {}) }
  next[indicatorKey] = !next[indicatorKey]
  expandedIndicators.value = next
}

function addFieldToPlaceholder(fieldKey) {
  const rows = mappingForm.value.config.word_placeholders || []
  const token = fieldKey
  const exists = rows.some((r) => (r.field_key === fieldKey) || ((r.placeholder || '').trim() === token))
  if (exists) return
  rows.push({ placeholder: token, field_key: fieldKey })
  mappingForm.value.config.word_placeholders = rows
}

function addAllModuleCommonFields(moduleNode) {
  for (const ind of moduleNode.children || []) {
    addAllIndicatorCommonFields(ind)
  }
}

function addAllIndicatorCommonFields(indicatorNode) {
  for (const f of indicatorNode.fields || []) {
    if (f.is_common || f.split_type === 'agg_score') {
      addFieldToPlaceholder(f.key)
    }
  }
}

/**
 * Recursively collect all is_common / agg_score field keys from a node
 * and all its descendants, then add them to the Word placeholder list.
 * Used by the new ExportFieldTreeNode "直接加入常用" / "全选本模块" button.
 */
function addAllNodeCommonFields(node) {
  function collect(n) {
    for (const f of n.fields || []) {
      if (f.is_common || f.split_type === 'agg_score') {
        addFieldToPlaceholder(f.key)
      }
    }
    for (const child of n.children || []) collect(child)
  }
  collect(node)
}

/**
 * Handle toggle-field event from ExportFieldTreeNode.
 * Supports optional mode: 'select' | 'deselect' | undefined (toggle).
 */
function onTreeToggleField(key, mode) {
  const s = new Set(selectedFieldKeys.value)
  if (mode === 'select') {
    s.add(key)
  } else if (mode === 'deselect') {
    s.delete(key)
  } else {
    s.has(key) ? s.delete(key) : s.add(key)
  }
  selectedFieldKeys.value = s
}

function toggleFieldSelection(key) {
  const s = new Set(selectedFieldKeys.value)
  s.has(key) ? s.delete(key) : s.add(key)
  selectedFieldKeys.value = s
}

function isFieldSelected(key) {
  return selectedFieldKeys.value.has(key)
}

function selectAllIndicatorFields(indicatorNode) {
  const s = new Set(selectedFieldKeys.value)
  for (const f of indicatorNode.fields || []) {
    s.add(f.key)
  }
  selectedFieldKeys.value = s
}

function deselectAllIndicatorFields(indicatorNode) {
  const s = new Set(selectedFieldKeys.value)
  for (const f of indicatorNode.fields || []) {
    s.delete(f.key)
  }
  selectedFieldKeys.value = s
}

function isIndicatorAllSelected(indicatorNode) {
  return (indicatorNode.fields || []).length > 0 && (indicatorNode.fields || []).every((f) => selectedFieldKeys.value.has(f.key))
}

function isIndicatorPartialSelected(indicatorNode) {
  const fields = indicatorNode.fields || []
  const count = fields.filter((f) => selectedFieldKeys.value.has(f.key)).length
  return count > 0 && count < fields.length
}

function selectAllModuleFields(moduleNode) {
  const s = new Set(selectedFieldKeys.value)
  for (const ind of moduleNode.children || []) {
    for (const f of ind.fields || []) s.add(f.key)
  }
  selectedFieldKeys.value = s
}

function isModuleAllSelected(moduleNode) {
  const allFields = (moduleNode.children || []).flatMap((ind) => ind.fields || [])
  return allFields.length > 0 && allFields.every((f) => selectedFieldKeys.value.has(f.key))
}

function clearFieldSelection() {
  selectedFieldKeys.value = new Set()
}

function batchAddToWordPlaceholders() {
  for (const key of selectedFieldKeys.value) {
    addFieldToPlaceholder(key)
  }
  selectedFieldKeys.value = new Set()
}

function batchAddToExcelColumns() {
  for (const key of selectedFieldKeys.value) {
    const label = getFieldDisplayName(key)
    mappingForm.value.config.excel_columns.push({ column: '', field_key: key, header: label })
  }
  selectedFieldKeys.value = new Set()
}

function isModuleChecked(moduleKey) {
  return presetForm.value.modules.includes(moduleKey)
}

function togglePresetModule(moduleKey) {
  const list = [...presetForm.value.modules]
  const idx = list.indexOf(moduleKey)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(moduleKey)
  presetForm.value.modules = list.sort()
}

function quickGeneratePreset() {
  quickAddIndicatorCommonPlaceholders()
}

/**
 * @description 套用后端内置“长表默认模板预设”，并按模块勾选做二次筛选。
 * @returns {void}
 */
function applyBuiltInLongFormPreset() {
  const preset = (exportPresets.value || []).find((item) => item.id === 'long_form_default')
  if (!preset) {
    quickGeneratePreset()
    return
  }
  const rows = []
  const selectedModules = new Set((presetForm.value.modules || []).map((m) => String(m).toUpperCase()))
  const includeBase = !!presetForm.value.include_base
  const allFields = allExportFields.value || []
  const fieldMetaMap = new Map(allFields.map((f) => [f.key, f]))
  for (const item of preset.word_placeholders || []) {
    const fieldKey = item.field_key
    const fieldMeta = fieldMetaMap.get(fieldKey)
    if (!fieldMeta) continue
    const isIndicator = fieldMeta.category_id === 'indicators'
    if (!isIndicator && !includeBase) continue
    if (isIndicator) {
      const mk = String(fieldMeta.module_key || '').toUpperCase()
      if (!selectedModules.has(mk)) continue
    }
    rows.push({
      placeholder: String(item.placeholder || '').trim(),
      field_key: fieldKey,
    })
  }
  const oldRows = mappingForm.value.config.word_placeholders || []
  const seen = new Set(oldRows.map((r) => `${String(r.placeholder || '').trim()}|${r.field_key || ''}`))
  const merged = [...oldRows]
  for (const row of rows) {
    const key = `${row.placeholder}|${row.field_key}`
    if (seen.has(key)) continue
    merged.push(row)
    seen.add(key)
  }
  mappingForm.value.config.word_placeholders = merged
}

function getFieldDisplayName(fieldKey) {
  const all = allExportFields.value || []
  const hit = all.find((f) => f.key === fieldKey)
  return hit?.label || fieldKey
}

function ensureTreeExpanded() {
  // Default: all collapsed. Only set state if not already initialized.
  if (Object.keys(expandedModules.value).length === 0) {
    expandedModules.value = {}
  }
  if (Object.keys(expandedIndicators.value).length === 0) {
    expandedIndicators.value = {}
  }
}

function applyTreeFallbackFromFlat() {
  if ((fieldTree.value || []).length > 0) return
  const indicators = (allExportFields.value || []).filter((f) => f.category_id === 'indicators')
  const moduleMap = new Map()
  for (const f of indicators) {
    const mk = f.module_key || 'Z'
    if (!moduleMap.has(mk)) {
      moduleMap.set(mk, { module_key: mk, module_label: f.module_label || mk, module_code: f.module_code || '', module_order: f.module_order || 999, children: [] })
    }
    const mod = moduleMap.get(mk)
    if (!mod.module_code && f.module_code) mod.module_code = f.module_code
    let ind = mod.children.find((x) => String(x.indicator_id) === String(f.indicator_id))
    if (!ind) {
      ind = {
        indicator_id: f.indicator_id,
        indicator_key: f.indicator_key || String(f.indicator_id),
        indicator_label: f.group_label || f.indicator_name || String(f.indicator_id),
        indicator_order: f.indicator_order || 999999,
        fields: [],
      }
      mod.children.push(ind)
    }
    ind.fields.push({ key: f.key, label: f.label, split_type: f.split_type, is_common: !!f.is_common, field_type_order: f.field_type_order || 999 })
  }
  const built = Array.from(moduleMap.values()).sort((a, b) => (a.module_order || 999) - (b.module_order || 999))
  for (const m of built) {
    m.children.sort((a, b) => (a.indicator_order || 999999) - (b.indicator_order || 999999))
    for (const ind of m.children) {
      ind.fields.sort((a, b) => (a.field_type_order || 999) - (b.field_type_order || 999))
    }
  }
  fieldTree.value = built
}

/**
 * 保存映射配置。
 * @returns {Promise<Object|null>}
 */
async function saveMapping() {
  configError.value = ''
  if (!selectedProjectId.value) return
  if (!mappingForm.value.name.trim()) {
    configError.value = '请填写映射名称'
    return null
  }
  const outputFormat = String(mappingForm.value.output_format || '').toLowerCase()
  if ((outputFormat === 'word' || outputFormat === 'pdf') && !selectedTemplateId.value) {
    configError.value = 'Word/PDF 映射必须绑定一个 Word 模板，请先选择模板'
    return null
  }
  savingMapping.value = true
  try {
    const payload = {
      name: mappingForm.value.name.trim(),
      project: selectedProjectId.value,
      template: selectedTemplateId.value || null,
      output_format: mappingForm.value.output_format,
      is_default: mappingForm.value.is_default,
      config: mappingForm.value.config,
    }
    let saved
    if (selectedMappingId.value) {
      saved = await updateExportMapping(selectedMappingId.value, payload)
      const idx = mappingList.value.findIndex((x) => x.id === saved.id)
      if (idx >= 0) mappingList.value[idx] = saved
    } else {
      saved = await createExportMapping(payload)
      mappingList.value.unshift(saved)
      selectedMappingId.value = saved.id
    }
    return saved
  } catch (e) {
    configError.value = e.response?.data?.detail ?? '保存映射失败'
    return null
  } finally {
    savingMapping.value = false
  }
}

/**
 * @description 导出前确保当前配置已持久化，避免“配置已改但未保存”导致导出失败。
 * @returns {Promise<void>}
 */
async function ensureMappingReadyForExport() {
  if (!mappingForm.value.name?.trim()) {
    mappingForm.value.name = `默认导出映射_${selectedProjectName.value || selectedProjectId.value}`
  }
  const saved = await saveMapping()
  if (!saved || !selectedMappingId.value) {
    throw new Error('映射保存失败，请先保存映射后再导出')
  }
}

/**
 * 套用已选映射到编辑表单。
 * @returns {void}
 */
function applySelectedMapping() {
  if (!selectedMappingId.value) {
    mappingForm.value.name = ''
    mappingForm.value.output_format = 'xlsx'
    mappingForm.value.is_default = false
    mappingForm.value.config = normalizeMappingConfig()
    return
  }
  const selected = mappingList.value.find((x) => x.id === selectedMappingId.value)
  if (!selected) return
  mappingForm.value.name = selected.name
  mappingForm.value.output_format = selected.output_format
  mappingForm.value.is_default = !!selected.is_default
  mappingForm.value.config = normalizeMappingConfig(selected.config)
  fieldViewMode.value = mappingForm.value.config.field_view_mode || 'template_common_first'
  if (selected.template) {
    const exists = (templateList.value || []).some((t) => t.id === selected.template)
    if (exists) {
      selectedTemplateId.value = selected.template
    } else {
      selectedTemplateId.value = null
      configError.value = '所选映射绑定的模板已失效，请重新选择模板并保存映射'
    }
  }
}

/**
 * 使用当前模板映射配置导出。
 * @returns {Promise<void>}
 */
async function doConfiguredExport() {
  if (!selectedProjectId.value) return
  exporting.value = true
  exportError.value = ''
  configError.value = ''
  try {
    const outputFormat = String(mappingForm.value.output_format || '').toLowerCase()
    if ((outputFormat === 'word' || outputFormat === 'pdf') && !selectedTemplateId.value) {
      throw new Error('当前映射未绑定 Word 模板，请先在模板列表选择模板并保存映射')
    }
    await ensureMappingReadyForExport()
    const templateExists = (templateList.value || []).some((item) => item.id === selectedTemplateId.value)
    if (selectedTemplateId.value && !templateExists) {
      selectedTemplateId.value = null
      throw new Error('所选模板已失效，请重新选择模板并保存映射')
    }
    await exportReport(selectedProjectId.value, mappingForm.value.output_format, selectedProjectName.value, {
      mapping_id: selectedMappingId.value || undefined,
      ...(String(mappingForm.value.output_format || '').toLowerCase() !== 'xlsx' && pageExportMultiFile.value
        ? { multi_file: 'true' }
        : {}),
      ...(String(mappingForm.value.output_format || '').toLowerCase() !== 'xlsx' && pageExportMultiFile.value && pageExportGroupBy.value
        ? { group_by: pageExportGroupBy.value }
        : {}),
      ...getFilterParams(),
    })
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '配置导出失败'
    if (String(msg).includes('映射') && String(msg).includes('不存在')) {
      selectedMappingId.value = null
      configError.value = '所选映射已失效，已自动清空，请重新选择后再导出'
      await refreshTemplateAndMappings()
      exportError.value = configError.value
      return
    }
    if (String(msg).includes('模板') && String(msg).includes('不存在')) {
      selectedTemplateId.value = null
      configError.value = '所选模板已失效，已自动清空，请重新选择模板并保存映射'
      await refreshTemplateAndMappings()
      exportError.value = configError.value
      return
    }
    exportError.value = msg
    configError.value = msg
  } finally {
    exporting.value = false
  }
}

/**
 * @description 主页面按筛选+映射执行导出。
 * @returns {Promise<void>}
 */
async function doPageDrivenExport() {
  if (!selectedProjectId.value) return
  exporting.value = true
  exportError.value = ''
  try {
    const format = pageExportFormat.value
    const selected = pageExportMappingCandidates.value.find((x) => x.id === pageExportMappingId.value) || null
    const params = {
      ...getFilterParams(),
      mapping_id: selected?.id || undefined,
      ...(format !== 'xlsx' && pageExportMultiFile.value ? { multi_file: 'true' } : {}),
      ...(format !== 'xlsx' && pageExportMultiFile.value && pageExportGroupBy.value
        ? { group_by: pageExportGroupBy.value }
        : {}),
    }
    await exportReport(selectedProjectId.value, format, selectedProjectName.value, params)
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '导出失败'
    if (String(msg).includes('映射') && String(msg).includes('不存在')) {
      pageExportMappingId.value = null
      await refreshTemplateAndMappings()
      exportError.value = '默认映射已失效，已自动清空，请重新选择映射后再导出'
      return
    }
    if (String(msg).includes('模板') && String(msg).includes('不存在')) {
      pageExportMappingId.value = null
      await refreshTemplateAndMappings()
      exportError.value = '映射关联模板不存在，请到“导出模板配置”中重新绑定模板并保存'
      return
    }
    exportError.value = msg
  } finally {
    exporting.value = false
  }
}

// ====== 工具函数 ======

/**
 * @description 提交状态中文标签（兼容后端派生展示态）。
 * @param {{ submission: Object, final_score: number|null }} item
 * @returns {string}
 */
function statusLabel(item) {
  return deriveSubmissionDisplayStatus({
    ...(item?.submission || {}),
    final_score: item?.final_score,
  }).label
}

/**
 * @description 进入学生成绩报表详情页。
 * @param {number} submissionId
 * @returns {void}
 */
function goSubmissionDetail(submissionId) {
  router.push({ name: 'ReportSubmissionDetail', params: { id: submissionId } })
}

/**
 * 排名徽章样式：前三名金/银/铜
 * @param {number} rank
 */
function rankBadgeClass(rank) {
  if (rank === 1) return 'bg-amber-400 text-white'
  if (rank === 2) return 'bg-slate-400 text-white'
  if (rank === 3) return 'bg-orange-400 text-white'
  return 'bg-slate-100 text-slate-600'
}

/**
 * @description 主页面导出格式变化时校准映射与打包选项。
 * @returns {void}
 */
function onPageExportFormatChange() {
  const exists = pageExportMappingCandidates.value.some((x) => x.id === pageExportMappingId.value)
  if (!exists) {
    const prefer = pageExportMappingCandidates.value.find((x) => x.is_default) || pageExportMappingCandidates.value[0]
    pageExportMappingId.value = prefer?.id ?? null
  }
}

useRealtimeRefresh('score', () => {
  if (isStudent.value) loadMyReport()
  else if (isDirectorOrAdmin.value || isCounselor.value) loadSeasons()
})

// 选择/取消 Excel 模板时自动切换 write_header 默认值：
// 有模板时默认不写表头（保留模板合并标题行）；无模板时默认写表头。
watch(selectedTemplateId, (newId) => {
  if (mappingForm.value.output_format === 'xlsx') {
    // 只在用户未手动改过时（即仍是"默认"值）才自动切换
    const cfg = mappingForm.value.config
    if (newId) {
      cfg.write_header = false
    } else {
      cfg.write_header = true
    }
  }
})

onMounted(() => {
  if (isStudent.value) {
    loadMyReport()
  } else if (isDirectorOrAdmin.value || isCounselor.value) {
    loadSeasons()
    loadDepartmentOptions()
    loadMajorOptions()
    loadClassOptions()
  }
})
</script>
