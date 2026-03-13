<template>
  <div class="page-shell" @click="onPageClick">
    <div class="flex items-center justify-between gap-2">
      <h3 class="app-page-title hidden md:block">用户管理</h3>
      <div class="flex flex-1 md:flex-none flex-wrap items-center gap-2">
        <router-link
          :to="{ name: 'UserImport' }"
          class="app-btn app-btn-secondary app-btn-sm flex-1 md:flex-none"
        >
          批量导入
        </router-link>
        <button
          type="button"
          class="app-btn app-btn-primary app-btn-sm flex-1 md:flex-none"
          @click.stop="goToCreate"
        >
          新建用户
        </button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="app-surface p-3 md:p-4">
      <div class="app-filter-wrap !lg:grid-cols-5">
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>状态</span>
        <select v-model="filterIsActive" class="app-select">
          <option value="">全部</option>
          <option value="true">启用</option>
          <option value="false">禁用</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>院系</span>
        <select v-model="filterDepartment" class="app-select">
          <option value="">全部</option>
          <option v-for="d in flatDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>专业</span>
        <select v-model="filterMajor" class="app-select">
          <option value="">全部</option>
          <option v-for="m in majorList" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>年级</span>
        <select v-model="filterGrade" class="app-select">
          <option value="">全部</option>
          <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>班级</span>
        <select v-model="filterClass" class="app-select">
          <option value="">全部</option>
          <option v-for="c in classList" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>角色</span>
        <select v-model="filterRole" class="app-select">
          <option value="">全部</option>
          <option v-for="r in roleList" :key="r.id" :value="r.id">{{ r.name }}</option>
        </select>
      </label>
      <label class="flex flex-col gap-1 text-sm text-slate-600">
        <span>关键字</span>
        <input v-model="filterSearch" type="text" placeholder="用户名/姓名/学号/工号" class="app-input" />
      </label>
      <button
        type="button"
        class="inline-flex h-10 w-auto min-w-24 self-end items-center justify-center rounded bg-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-300"
        @click="onSearch"
      >
        查询
      </button>
      </div>
    </div>

    <div v-if="bulkActionVisible" class="app-surface p-3 md:p-4 hidden md:block">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div class="text-sm text-slate-600">
          已选 <span class="font-semibold text-slate-800">{{ selectedCount }}</span> 人
          <span class="ml-2 text-xs text-slate-400">（不包含当前登录账号）</span>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="selectedCount < 2 || bulkLoading"
            @click="onBatchSetActive(true)"
          >
            批量启用
          </button>
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="selectedCount < 2 || bulkLoading"
            @click="onBatchSetActive(false)"
          >
            批量禁用
          </button>
          <input
            v-model="batchPassword"
            type="text"
            placeholder="新密码（至少6位）"
            class="app-input h-9 w-48"
          />
          <button
            type="button"
            class="rounded border border-amber-300 px-3 py-1.5 text-sm text-amber-700 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="selectedCount < 2 || bulkLoading"
            @click="onBatchResetPassword"
          >
            批量重置密码
          </button>
          <select v-model="batchRoleId" class="app-select h-9 w-44">
            <option value="">选择角色</option>
            <option v-for="r in assignableRoleList" :key="r.id" :value="String(r.id)">{{ r.name }}</option>
          </select>
          <button
            type="button"
            class="app-btn app-btn-secondary app-btn-sm disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="selectedCount < 2 || !batchRoleId || bulkLoading"
            @click="onBatchSetRole"
          >
            批量改角色
          </button>
          <button
            type="button"
            class="rounded border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="selectedCount < 2 || bulkLoading"
            @click="onBatchDelete"
          >
            批量删除
          </button>
          <button
            type="button"
            class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!selectedCount || bulkLoading"
            @click="clearSelection"
          >
            清空已选
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="rounded border border-slate-200 bg-white py-12 text-center text-slate-500">加载中…</div>
    <div v-else-if="listError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ listError }}</div>
    <div v-else class="space-y-2 relative">
      <div v-if="paginating" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60 rounded-xl">
        <span class="text-sm text-slate-400">加载中…</span>
      </div>
      <div class="mobile-card-list">
        <div
          v-for="u in userList"
          :key="`mobile-${u.id}`"
          class="mobile-card"
          :class="u.id === lastEditedId ? 'bg-blue-50' : ''"
        >
          <div class="flex items-start gap-3" @click="goToEdit(u.id)">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="mobile-card-title">{{ fullName(u) }}</span>
                <span class="flex-shrink-0 rounded px-1.5 py-0.5 text-[10px]" :class="u.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'">
                  {{ u.is_active ? '启用' : '禁用' }}
                </span>
              </div>
              <div class="mobile-card-sub">{{ u.username }} · {{ roleNamesDisplay(u) }}</div>
              <div class="mobile-card-meta">{{ u.department_name || '—' }} · {{ u.student_no || u.employee_no || '—' }}</div>
            </div>
            <svg class="mobile-card-arrow mt-1 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" /></svg>
          </div>
          <div class="mt-2 flex gap-2 border-t border-slate-100 pt-2">
            <button type="button" class="app-action app-action-default flex-1" @click.stop="goToEdit(u.id)">编辑</button>
            <button type="button" class="app-action app-action-danger flex-1" @click.stop="onDeleteUser(u)">删除</button>
          </div>
        </div>
      </div>
      <div class="app-table-wrap hidden md:block">
      <table class="app-table min-w-[1400px] table-auto">
        <thead>
          <tr class="border-b border-slate-200 bg-slate-50">
            <th class="px-3 py-2.5 text-left font-medium text-slate-700">
              <input
                type="checkbox"
                :checked="isAllCurrentPageSelected"
                :disabled="!selectableCurrentPageIds.length"
                @change="toggleSelectAllCurrentPage"
              />
            </th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">用户名</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">姓名</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">学号/工号</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">性别</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">院系</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">专业</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">年级</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">班级</th>
            <th class="px-4 py-2.5 text-left font-medium text-slate-700">角色</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">状态</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">登录状态</th>
            <th class="whitespace-nowrap px-4 py-2.5 text-left font-medium text-slate-700">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="u in userList"
            :key="u.id"
            class="border-b border-slate-100 transition-colors"
            :class="u.id === lastEditedId ? 'bg-blue-50' : 'hover:bg-slate-50'"
          >
            <td class="px-3 py-2.5">
              <input
                type="checkbox"
                :checked="selectedUserIds.includes(u.id)"
                :disabled="!isRowSelectable(u)"
                @change="toggleUserSelection(u)"
              />
            </td>
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-800">{{ u.username }}</td>
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-800">{{ fullName(u) }}</td>
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">{{ u.student_no || u.employee_no || '—' }}</td>
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">{{ u.gender_label || '未知' }}</td>
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">{{ u.department_name || '—' }}</td>
            <!-- 专业：学生显示所在专业；非学生从负责班级推导唯一专业列表 -->
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">
              <template v-if="isStudent(u)">{{ u.class_major_name || '—' }}</template>
              <template v-else-if="uniqueMajors(u).length === 1">{{ uniqueMajors(u)[0] }}</template>
              <template v-else-if="uniqueMajors(u).length > 1">
                <span
                  class="cursor-default border-b border-dashed border-slate-400 text-slate-700 hover:text-brand-600 hover:border-brand-400 transition-colors"
                  @mouseenter="showTooltip($event, u.id, 'major')"
                  @mouseleave="hideTooltip"
                >{{ uniqueMajors(u).length }}个专业</span>
              </template>
              <template v-else>—</template>
            </td>
            <!-- 年级：学生显示班级年级；非学生从负责班级推导唯一年级列表 -->
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">
              <template v-if="isStudent(u)">{{ u.class_grade || '—' }}</template>
              <template v-else-if="uniqueGrades(u).length === 1">{{ uniqueGrades(u)[0] }}</template>
              <template v-else-if="uniqueGrades(u).length > 1">
                <span
                  class="cursor-default border-b border-dashed border-slate-400 text-slate-700 hover:text-brand-600 hover:border-brand-400 transition-colors"
                  @mouseenter="showTooltip($event, u.id, 'grade')"
                  @mouseleave="hideTooltip"
                >{{ uniqueGrades(u).length }}个年级</span>
              </template>
              <template v-else>—</template>
            </td>
            <!-- 班级：学生显示班级名；非学生显示负责班级数量（hover 展开卡片）-->
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">
              <template v-if="isStudent(u)">{{ u.class_name || '—' }}</template>
              <template v-else-if="u.responsible_classes?.length">
                <span
                  class="cursor-default border-b border-dashed border-slate-400 text-slate-700 hover:text-brand-600 hover:border-brand-400 transition-colors"
                  @mouseenter="showTooltip($event, u.id, 'class')"
                  @mouseleave="hideTooltip"
                >{{ u.responsible_classes.length }}个班级</span>
              </template>
              <template v-else>—</template>
            </td>
            <td class="whitespace-nowrap px-4 py-2.5 text-slate-600">{{ roleNamesDisplay(u) }}</td>
            <td class="whitespace-nowrap px-4 py-2.5">
              <span class="rounded px-2 py-0.5 text-xs" :class="u.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'">
                {{ u.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-2.5">
              <span
                class="rounded px-2 py-0.5 text-xs"
                :class="hasLoggedIn(u) ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'"
                :title="u.id === authStore.user?.id ? '当前登录' : (hasLoggedIn(u) && u.last_login ? formatDateTime(u.last_login) : '')"
              >
                {{ hasLoggedIn(u) ? '已登录' : '未登录' }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-2.5">
              <button
                type="button"
                class="app-action app-action-default"
                @click.stop="goToEdit(u.id)"
              >
                编辑
              </button>
              <button
                type="button"
                class="ml-2 app-action app-action-danger"
                @click.stop="onDeleteUser(u)"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="userList.length === 0">
            <td colspan="13" class="px-4 py-8 text-center text-slate-500">暂无用户，可调整筛选条件或点击「新建用户」</td>
          </tr>
        </tbody>
      </table>
      </div>
      <!-- 分页 -->
      <div v-if="totalCount > 0" class="flex items-center justify-between border-t border-slate-200 px-4 py-2 text-sm text-slate-600">
        <span>共 {{ totalCount }} 条</span>
        <div class="flex gap-2">
          <button type="button" class="rounded border border-slate-300 px-2.5 py-1 hover:bg-slate-50 disabled:opacity-50" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</button>
          <span class="flex items-center px-2">{{ currentPage }} / {{ totalPages }}</span>
          <button type="button" class="rounded border border-slate-300 px-2.5 py-1 hover:bg-slate-50 disabled:opacity-50" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 非学生用户 专业/年级/班级 统一悬浮卡：渲染到 body 避免 overflow:hidden 裁切 -->
  <Teleport to="body">
    <div
      v-if="hoveredUserId && tooltipItems.length"
      class="pointer-events-none fixed z-50 min-w-[160px] max-w-[280px] rounded-lg border border-slate-200 bg-white px-3 py-2.5 shadow-xl text-sm"
      :style="tooltipPos"
    >
      <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ tooltipTitle }}</p>
      <ul class="space-y-1">
        <li v-for="(item, idx) in tooltipItems" :key="idx" class="flex flex-col">
          <span class="font-medium text-slate-800">{{ item.primary }}</span>
          <span v-if="item.secondary" class="text-xs text-slate-500">{{ item.secondary }}</span>
        </li>
      </ul>
    </div>
  </Teleport>
</template>

<script setup>
/**
 * 用户列表页：表格、筛选、分页。
 * 从编辑页返回时恢复页码与筛选条件，并高亮刚编辑的行（点击页面任意处后消失）。
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'
import { useUserListStore } from '@/stores/userList'
import {
  getUsers,
  getRoles,
  deleteUser,
  batchSetUserActive,
  batchResetUserPassword,
  batchSetUserRole,
  batchDeleteUsers,
} from '@/api/users'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { formatDateTime } from '@/utils/format'

const authStore = useAuthStore()
const userListStore = useUserListStore()
const router = useRouter()
const route = useRoute()
const PAGE_SIZE = 20

const loading = ref(false)
const paginating = ref(false)
const listError = ref('')
const userList = ref([])
const totalCount = ref(0)
const currentPage = ref(1)

const filterIsActive = ref('')
const filterDepartment = ref('')
const filterMajor = ref('')
const filterGrade = ref('')
const filterClass = ref('')
const filterRole = ref('')
const filterSearch = ref('')

const departmentTree = ref([])
const majorList = ref([])
const classList = ref([])
const roleList = ref([])
const selectedUserIds = ref([])
const bulkLoading = ref(false)
const batchPassword = ref('')
const batchRoleId = ref('')

/** 刚编辑/创建的用户 ID（浅蓝高亮行），点击页面任意处后清除 */
const lastEditedId = ref(null)

/** 当前触发悬浮卡的用户 ID */
const hoveredUserId = ref(null)
/** 当前触发的列类型：'major' | 'grade' | 'class' */
const hoveredColumn = ref(null)
/** 悬浮卡定位（fixed 坐标）*/
const tooltipPos = ref({ top: '0px', left: '0px' })
const isApplyingRouteState = ref(false)

/** 悬浮卡标题（根据触发列动态切换） */
const tooltipTitle = computed(() => {
  const map = { major: '负责专业', grade: '负责年级', class: '负责班级' }
  return map[hoveredColumn.value] ?? ''
})

/** 悬浮卡条目（根据触发列动态生成） */
const tooltipItems = computed(() => {
  if (!hoveredUserId.value) return []
  const u = userList.value.find((u) => u.id === hoveredUserId.value)
  const classes = u?.responsible_classes ?? []
  if (!classes.length) return []
  if (hoveredColumn.value === 'class') {
    return classes.map((c) => ({
      primary: c.name,
      secondary: [c.grade ? c.grade + '年' : '', c.major_name].filter(Boolean).join(' · '),
    }))
  }
  if (hoveredColumn.value === 'major') {
    return [...new Set(classes.map((c) => c.major_name).filter(Boolean))].map((name) => ({
      primary: name,
      secondary: '',
    }))
  }
  if (hoveredColumn.value === 'grade') {
    return [...new Set(classes.map((c) => c.grade).filter(Boolean))]
      .sort()
      .map((g) => ({ primary: g, secondary: '' }))
  }
  return []
})

const gradeOptions = computed(() => {
  const set = new Set(classList.value.map((c) => c.grade).filter(Boolean))
  return [...set].sort()
})

function flattenDepartments(nodes) {
  const list = []
  function collect(n) {
    for (const node of n) {
      list.push({ id: node.id, name: node.name })
      if (node.children?.length) collect(node.children)
    }
  }
  collect(nodes)
  return list
}

const flatDepartments = computed(() => flattenDepartments(departmentTree.value))
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))
const selectedCount = computed(() => selectedUserIds.value.length)
const bulkActionVisible = computed(() => selectedCount.value >= 2)
const assignableRoleList = computed(() => roleList.value.filter((r) => Number(r.level) < 5))
const selectableCurrentPageIds = computed(() =>
  userList.value.filter((u) => isRowSelectable(u)).map((u) => u.id)
)
const isAllCurrentPageSelected = computed(() => {
  if (!selectableCurrentPageIds.value.length) return false
  return selectableCurrentPageIds.value.every((id) => selectedUserIds.value.includes(id))
})

/**
 * 当前 URL 是否带有用户列表状态 query。
 * @returns {boolean}
 */
function hasListQueryInUrl() {
  const q = route.query
  return ['page', 'is_active', 'department', 'major', 'grade', 'class_obj', 'role', 'search']
    .some((k) => q[k] !== undefined)
}

/**
 * 从路由 query 还原页码和筛选条件。
 */
function applyStateFromRouteQuery() {
  const q = route.query
  isApplyingRouteState.value = true
  try {
    const p = Number(q.page)
    currentPage.value = Number.isFinite(p) && p > 0 ? p : 1
    filterIsActive.value = typeof q.is_active === 'string' ? q.is_active : ''
    filterDepartment.value = typeof q.department === 'string' ? q.department : ''
    filterMajor.value = typeof q.major === 'string' ? q.major : ''
    filterGrade.value = typeof q.grade === 'string' ? q.grade : ''
    filterClass.value = typeof q.class_obj === 'string' ? q.class_obj : ''
    filterRole.value = typeof q.role === 'string' ? q.role : ''
    filterSearch.value = typeof q.search === 'string' ? q.search : ''
  } finally {
    isApplyingRouteState.value = false
  }
}

/**
 * 将当前页码与筛选条件同步到 URL，支持刷新后原位恢复。
 */
function syncStateToRouteQuery() {
  const query = {}
  if (currentPage.value > 1) query.page = String(currentPage.value)
  if (filterIsActive.value !== '') query.is_active = String(filterIsActive.value)
  if (filterDepartment.value) query.department = String(filterDepartment.value)
  if (filterMajor.value) query.major = String(filterMajor.value)
  if (filterGrade.value) query.grade = String(filterGrade.value)
  if (filterClass.value) query.class_obj = String(filterClass.value)
  if (filterRole.value) query.role = String(filterRole.value)
  if (filterSearch.value.trim()) query.search = filterSearch.value.trim()
  router.replace({ query })
}

function fullName(u) {
  return u.name || '—'
}

/**
 * 是否为学生用户（有 class_obj 即视为学生，展示班级/专业/年级列）。
 * @param {object} u
 */
function isStudent(u) {
  return !!u.class_obj
}

/**
 * 从负责班级中提取唯一专业名列表（非学生用）。
 * @param {object} u
 */
function uniqueMajors(u) {
  return [...new Set((u.responsible_classes ?? []).map((c) => c.major_name).filter(Boolean))]
}

/**
 * 从负责班级中提取唯一年级列表（非学生用）。
 * @param {object} u
 */
function uniqueGrades(u) {
  return [...new Set((u.responsible_classes ?? []).map((c) => c.grade).filter(Boolean))].sort()
}

/**
 * 显示悬浮卡，定位于触发元素正下方。
 * @param {MouseEvent} event
 * @param {number} userId
 * @param {'major'|'grade'|'class'} column - 触发列类型
 */
function showTooltip(event, userId, column) {
  hoveredUserId.value = userId
  hoveredColumn.value = column
  const rect = event.currentTarget.getBoundingClientRect()
  tooltipPos.value = {
    top: `${rect.bottom + 6}px`,
    left: `${Math.min(rect.left, window.innerWidth - 280)}px`,
  }
}

/** 隐藏悬浮卡 */
function hideTooltip() {
  hoveredUserId.value = null
  hoveredColumn.value = null
}

function roleNamesDisplay(u) {
  const names = u.role_names
  return names?.length ? names.join('、') : '—'
}

function hasLoggedIn(u) {
  if (u == null) return false
  if (authStore.user?.id != null && u.id === authStore.user.id) return true
  return u.last_login != null && u.last_login !== ''
}

/**
 * 当前行是否允许批量选择。
 * @param {object} u
 * @returns {boolean}
 */
function isRowSelectable(u) {
  return u?.id != null && u.id !== authStore.user?.id
}

/**
 * 单行勾选切换。
 * @param {object} u
 */
function toggleUserSelection(u) {
  if (!isRowSelectable(u)) return
  const id = u.id
  if (selectedUserIds.value.includes(id)) {
    selectedUserIds.value = selectedUserIds.value.filter((v) => v !== id)
    return
  }
  selectedUserIds.value = [...selectedUserIds.value, id]
}

/** 当前页全选/反选（仅可选行）。 */
function toggleSelectAllCurrentPage() {
  if (!selectableCurrentPageIds.value.length) return
  if (isAllCurrentPageSelected.value) {
    selectedUserIds.value = selectedUserIds.value.filter(
      (id) => !selectableCurrentPageIds.value.includes(id)
    )
    return
  }
  const merged = new Set([...selectedUserIds.value, ...selectableCurrentPageIds.value])
  selectedUserIds.value = [...merged]
}

/** 清空所有已选用户（跨页）。 */
function clearSelection() {
  selectedUserIds.value = []
}

/**
 * 批量启用/禁用。
 * @param {boolean} isActive
 */
async function onBatchSetActive(isActive) {
  if (selectedCount.value < 2) return
  const actionName = isActive ? '启用' : '禁用'
  if (!window.confirm(`确定批量${actionName}选中的 ${selectedCount.value} 个用户吗？`)) return
  bulkLoading.value = true
  try {
    await batchSetUserActive(selectedUserIds.value, isActive)
    selectedUserIds.value = []
    await loadUsers()
    window.alert(`批量${actionName}成功`)
  } catch (e) {
    window.alert(e.response?.data?.detail ?? `批量${actionName}失败`)
  } finally {
    bulkLoading.value = false
  }
}

/** 批量重置密码。 */
async function onBatchResetPassword() {
  if (selectedCount.value < 2) return
  const pwd = batchPassword.value.trim()
  if (pwd.length < 6) {
    window.alert('请输入至少 6 位的新密码')
    return
  }
  if (!window.confirm(`确定将选中 ${selectedCount.value} 个用户密码重置为当前输入值吗？`)) return
  bulkLoading.value = true
  try {
    await batchResetUserPassword(selectedUserIds.value, pwd)
    batchPassword.value = ''
    selectedUserIds.value = []
    await loadUsers()
    window.alert('批量重置密码成功')
  } catch (e) {
    window.alert(e.response?.data?.detail ?? '批量重置密码失败')
  } finally {
    bulkLoading.value = false
  }
}

/** 批量重设角色。 */
async function onBatchSetRole() {
  if (selectedCount.value < 2 || !batchRoleId.value) return
  const role = assignableRoleList.value.find((r) => String(r.id) === String(batchRoleId.value))
  if (!role) {
    window.alert('请选择有效角色')
    return
  }
  if (!window.confirm(`确定将选中 ${selectedCount.value} 个用户统一改为「${role.name}」吗？`)) return
  bulkLoading.value = true
  try {
    await batchSetUserRole(selectedUserIds.value, [Number(batchRoleId.value)], [])
    selectedUserIds.value = []
    await loadUsers()
    window.alert('批量改角色成功')
  } catch (e) {
    window.alert(e.response?.data?.detail ?? '批量改角色失败')
  } finally {
    bulkLoading.value = false
  }
}

/** 批量删除用户。 */
async function onBatchDelete() {
  if (selectedCount.value < 2) return
  if (!window.confirm(`确定永久删除选中的 ${selectedCount.value} 个用户吗？该操作不可恢复。`)) return
  bulkLoading.value = true
  try {
    await batchDeleteUsers(selectedUserIds.value)
    selectedUserIds.value = []
    await loadUsers()
    window.alert('批量删除成功')
  } catch (e) {
    window.alert(e.response?.data?.detail ?? '批量删除失败')
  } finally {
    bulkLoading.value = false
  }
}

/**
 * 单个删除用户。
 * @param {object} u
 */
async function onDeleteUser(u) {
  if (!u?.id) return
  const displayName = fullName(u) === '—' ? u.username : `${fullName(u)}（${u.username}）`
  if (!window.confirm(`确定删除用户 ${displayName} 吗？该操作不可恢复。`)) return
  try {
    await deleteUser(u.id)
    selectedUserIds.value = selectedUserIds.value.filter((id) => id !== u.id)
    await loadUsers()
    window.alert('删除成功')
  } catch (e) {
    window.alert(e.response?.data?.detail ?? '删除失败')
  }
}

/**
 * 是否为 DRF 分页无效页错误。
 * @param {any} e
 * @returns {boolean}
 */
function isInvalidPageError(e) {
  const status = e?.response?.status
  const detail = String(e?.response?.data?.detail ?? '')
  if (status !== 404) return false
  return /invalid page|无效页|页码无效/i.test(detail)
}

/** 点击页面任意处（非阻止冒泡的元素）时清除高亮 */
function onPageClick() {
  if (lastEditedId.value !== null) {
    lastEditedId.value = null
    userListStore.clearLastEdited()
  }
}

/**
 * 加载用户列表；若当前页无效会自动回退到上一有效页。
 * @param {number} retryCount - 递归回退次数
 */
async function loadUsers(retryCount = 0, { softLoad = false } = {}) {
  if (softLoad) {
    paginating.value = true
  } else {
    loading.value = true
  }
  listError.value = ''
  try {
    const params = { page: currentPage.value, page_size: PAGE_SIZE }
    if (filterIsActive.value !== '') params.is_active = filterIsActive.value
    if (filterDepartment.value) params.department = filterDepartment.value
    if (filterMajor.value) params.major = filterMajor.value
    if (filterGrade.value) params.grade = filterGrade.value
    if (filterClass.value) params.class_obj = filterClass.value
    if (filterRole.value) params.role = filterRole.value
    if (filterSearch.value.trim()) params.search = filterSearch.value.trim()
    const data = await getUsers(params)
    userList.value = data.results ?? []
    totalCount.value = data.count ?? 0
  } catch (e) {
    if (isInvalidPageError(e) && currentPage.value > 1 && retryCount < 20) {
      currentPage.value -= 1
      syncStateToRouteQuery()
      return await loadUsers(retryCount + 1)
    }
    listError.value = e.response?.data?.detail ?? '加载用户列表失败'
    userList.value = []
    totalCount.value = 0
    selectedUserIds.value = []
  } finally {
    loading.value = false
    paginating.value = false
  }
}

function onSearch() {
  clearSelection()
  currentPage.value = 1
  syncStateToRouteQuery()
  loadUsers()
}

function goPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  syncStateToRouteQuery()
  loadUsers(0, { softLoad: true })
}

async function loadDepartments() {
  try {
    const { data } = await api.get('/departments/', { params: { tree: 1 } })
    departmentTree.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    departmentTree.value = []
  }
}

async function loadMajors() {
  try {
    const params = {}
    if (filterDepartment.value) params.department = filterDepartment.value
    const { data } = await api.get('/majors/', { params })
    majorList.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    majorList.value = []
  }
}

async function loadClasses() {
  try {
    const params = {}
    if (filterDepartment.value) params.department = filterDepartment.value
    if (filterMajor.value) params.major = filterMajor.value
    if (filterGrade.value) params.grade = filterGrade.value
    const { data } = await api.get('/classes/', { params })
    classList.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    classList.value = []
  }
}

watch([filterDepartment], () => {
  if (isApplyingRouteState.value) return
  filterMajor.value = ''
  filterGrade.value = ''
  filterClass.value = ''
  loadMajors()
  loadClasses()
})
watch([filterMajor, filterGrade], () => {
  if (isApplyingRouteState.value) return
  filterClass.value = ''
  loadClasses()
})

async function loadRoles() {
  try {
    roleList.value = await getRoles()
  } catch {
    roleList.value = []
  }
}

/**
 * 跳转到编辑页前保存当前列表状态到 store。
 * @param {number} userId
 */
function goToEdit(userId) {
  userListStore.saveListState(currentPage.value, {
    isActive: filterIsActive.value,
    department: filterDepartment.value,
    major: filterMajor.value,
    grade: filterGrade.value,
    class_obj: filterClass.value,
    role: filterRole.value,
    search: filterSearch.value,
  })
  router.push({ name: 'UserEdit', params: { id: userId } })
}

/** 跳转到新建用户页（同样保存当前状态，以便创建后返回） */
function goToCreate() {
  userListStore.saveListState(currentPage.value, {
    isActive: filterIsActive.value,
    department: filterDepartment.value,
    major: filterMajor.value,
    grade: filterGrade.value,
    class_obj: filterClass.value,
    role: filterRole.value,
    search: filterSearch.value,
  })
  router.push({ name: 'UserNew' })
}

onMounted(async () => {
  await loadDepartments()
  await loadRoles()

  if (hasListQueryInUrl()) {
    // 刷新/直达：优先从 URL 恢复列表状态（页码+筛选）
    applyStateFromRouteQuery()
    await loadMajors()
    await loadClasses()
    await loadUsers()
    return
  }

  if (userListStore.shouldRestore) {
    // 从编辑/创建页返回：恢复筛选和页码
    const f = userListStore.filters
    filterIsActive.value = f.isActive
    filterDepartment.value = f.department
    filterMajor.value = f.major
    filterGrade.value = f.grade
    filterClass.value = f.class_obj
    filterRole.value = f.role
    filterSearch.value = f.search
    currentPage.value = userListStore.page
    // 读取要高亮的用户 ID
    lastEditedId.value = userListStore.lastEditedId
    userListStore.shouldRestore = false
    syncStateToRouteQuery()

    // 加载依赖数据和用户列表
    await loadMajors()
    await loadClasses()
    await loadUsers()
  } else {
    await loadMajors()
    await loadClasses()
    await loadUsers()
  }
})

useRealtimeRefresh('user', () => loadUsers(0, { softLoad: true }))
</script>
