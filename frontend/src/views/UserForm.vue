<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <div class="flex items-center gap-2">
      <router-link :to="{ name: 'Users' }" class="text-slate-600 hover:text-slate-900">← 返回用户列表</router-link>
    </div>
    <h3 class="text-lg font-semibold text-slate-800">{{ isEdit ? '编辑用户' : '新建用户' }}</h3>

    <div v-if="loadError" class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ loadError }}</div>
    <form v-else class="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="submit">
      <!-- 统一表单项样式：标签 + 控件对齐 -->
      <!-- 基本信息 -->
      <section class="rounded-lg border border-slate-100 bg-slate-50/50 p-5">
        <h4 class="text-center text-xl font-semibold tracking-wide text-slate-800">基本信息</h4>
        <div class="mx-auto mt-3 mb-4 h-px max-w-[120px] bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
        <div class="grid gap-x-6 gap-y-4 sm:grid-cols-2">
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">用户名 <span class="text-red-500">*</span></label>
            <input v-model="form.username" type="text" required :readonly="isEdit" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-slate-100" placeholder="登录用户名" />
          </div>
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">密码 {{ isEdit ? '（不填则不修改）' : '' }}</label>
            <input v-model="form.password" :type="showPassword ? 'text' : 'password'" :required="!isEdit" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" :placeholder="isEdit ? '留空表示不修改' : '登录密码'" />
          </div>
          <div class="flex flex-col sm:col-span-2">
            <label class="mb-1.5 text-sm font-medium text-slate-700">邮箱</label>
            <input v-model="form.email" type="email" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder="选填" />
          </div>
          <div class="flex flex-col sm:col-span-2">
            <label class="mb-1.5 text-sm font-medium text-slate-700">姓名</label>
            <input v-model="form.name" type="text" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder="完整姓名" />
          </div>
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">手机</label>
            <input v-model="form.phone" type="text" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
          </div>
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">性别</label>
            <select v-model="form.gender" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
              <option value="">未知</option>
              <option value="M">男</option>
              <option value="F">女</option>
            </select>
          </div>
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">学号 / 工号</label>
            <input v-model="form.student_no" type="text" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder="学生填学号，教职工填工号" />
          </div>
        </div>
        <p class="mt-3 text-xs text-slate-500">学号/工号填其一即可。</p>
      </section>

      <!-- 组织与状态 -->
      <section class="rounded-lg border border-slate-100 bg-slate-50/50 p-5">
        <h4 class="text-center text-xl font-semibold tracking-wide text-slate-800">组织与状态</h4>
        <div class="mx-auto mt-3 mb-4 h-px max-w-[120px] bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
        <div class="grid gap-x-6 gap-y-4 sm:grid-cols-2">
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">院系</label>
            <select v-model="form.department" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @change="onDepartmentChange">
              <option value="">请选择</option>
              <option v-for="d in flatDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="flex flex-col">
            <span class="mb-1.5 block text-center text-sm font-medium text-slate-700">用户角色选择</span>
            <span class="mb-1.5 block text-center text-xs text-slate-500">（选最高身份即可，超级管理员在后台分配。）</span>
            <select v-model="form.primary_role_id" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
              <option value="">请选择</option>
              <option v-for="r in assignableRoles" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
          </div>
          <template v-if="isStudentRole">
            <div class="flex flex-col">
              <label class="mb-1.5 text-sm font-medium text-slate-700">专业</label>
              <select v-model="form.major" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @change="onMajorChange">
                <option value="">请选择</option>
                <option v-for="m in formMajorList" :key="m.id" :value="m.id">{{ m.name }}</option>
              </select>
            </div>
            <div class="flex flex-col">
              <label class="mb-1.5 text-sm font-medium text-slate-700">年级</label>
              <select v-model="form.grade" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @change="onGradeChange">
                <option value="">请选择</option>
                <option v-for="g in formGradeOptions" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
            <div class="flex flex-col">
              <label class="mb-1.5 text-sm font-medium text-slate-700">所在班级</label>
              <select v-model="form.class_obj" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
                <option value="">请选择</option>
                <option v-for="c in formClassList" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </template>
          <div class="flex flex-col">
            <label class="mb-1.5 text-sm font-medium text-slate-700">状态</label>
            <select v-model="form.is_active" class="rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
              <option :value="true">启用</option>
              <option :value="false">禁用</option>
            </select>
          </div>
        </div>
      </section>

      <!-- 非学生：负责班级选择器 -->
      <section v-if="form.primary_role_id && !isStudentRole" class="rounded-lg border border-slate-100 bg-slate-50/50 p-5">
        <h4 class="text-center text-xl font-semibold tracking-wide text-slate-800">负责班级</h4>
        <div class="mx-auto mt-3 mb-1 h-px max-w-[120px] bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
        <p class="mb-3 text-center text-xs text-slate-500">通过下方筛选添加，可跨专业、跨年级多选</p>

        <!-- 已选班级 chips -->
        <div class="mb-3">
          <div class="mb-1.5 flex items-center justify-between">
            <p class="text-sm text-slate-600">
              已选 <span class="font-medium text-slate-800">{{ selectedClasses.length }}</span> 个班级
            </p>
            <button
              v-if="selectedClasses.length"
              type="button"
              class="text-xs text-slate-400 hover:text-red-500"
              @click="selectedClasses = []"
            >清空全部</button>
          </div>
          <div v-if="selectedClasses.length" class="flex flex-wrap gap-1.5">
            <span
              v-for="c in selectedClasses"
              :key="c.id"
              class="inline-flex items-center gap-1 rounded border border-blue-200 bg-blue-50 px-2.5 py-1 text-sm text-blue-800"
            >
              {{ c.name }}
              <span class="text-xs text-blue-500">{{ c.grade ? `${c.grade}级` : '' }}</span>
              <span v-if="c.major_name" class="text-xs text-blue-400">· {{ c.major_name }}</span>
              <button type="button" class="ml-0.5 text-blue-400 hover:text-red-500 text-base leading-none" @click="removeFromSelection(c.id)">×</button>
            </span>
          </div>
          <p v-else class="text-sm text-slate-400">暂未选择任何负责班级</p>
        </div>

        <!-- 筛选选择器 -->
        <div class="rounded border border-slate-200 bg-slate-50 p-3">
          <p class="mb-2 text-xs font-medium text-slate-500">
            筛选条件（仅用于查找班级，不单独保存）
          </p>
          <div class="mb-2 flex flex-wrap items-center gap-2">
            <select
              v-model="pickerDept"
              class="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none min-w-[130px]"
              @change="onPickerDeptChange"
            >
              <option value="">全部院系</option>
              <option v-for="d in flatDepartments" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
            <select
              v-model="pickerMajor"
              class="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none min-w-[120px]"
              @change="onPickerMajorChange"
            >
              <option value="">全部专业</option>
              <option v-for="m in pickerMajorList" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
            <select
              v-model="pickerGrade"
              class="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-800 focus:border-brand-500 focus:outline-none min-w-[100px]"
              @change="loadPickerClasses"
            >
              <option value="">全部年级</option>
              <option v-for="g in pickerGradeOptions" :key="g" :value="g">{{ g }}</option>
            </select>
            <!-- 将当前筛选结果批量加入已选列表 -->
            <button
              v-if="pickerClassList.length > 0"
              type="button"
              class="ml-auto rounded border border-blue-300 bg-blue-50 px-3 py-1.5 text-xs text-blue-700 hover:bg-blue-100"
              :title="`将当前筛选出的 ${pickerClassList.length} 个班级全部加入`"
              @click="addAllPickerClasses"
            >全部添加（{{ pickerClassList.length }}个）</button>
          </div>

          <!-- 候选班级列表 -->
          <div v-if="pickerLoading" class="py-4 text-center text-xs text-slate-500">加载中…</div>
          <div v-else-if="pickerClassList.length === 0" class="py-4 text-center text-xs text-slate-400">暂无班级，请调整筛选条件</div>
          <div v-else class="max-h-48 overflow-y-auto rounded border border-slate-200 bg-white">
            <div
              v-for="c in pickerClassList"
              :key="c.id"
              class="flex items-center justify-between border-b border-slate-100 px-3 py-2 last:border-0"
              :class="isClassSelected(c.id) ? 'bg-blue-50' : 'hover:bg-slate-50'"
            >
              <div class="text-sm">
                <span class="text-slate-800">{{ c.name }}</span>
                <span v-if="c.department_name" class="ml-1.5 text-xs text-slate-500">{{ c.department_name }}</span>
                <span v-if="c.major_name" class="ml-1 text-xs text-slate-500">/ {{ c.major_name }}</span>
                <span v-if="c.grade" class="ml-1 text-xs text-slate-500">/ {{ c.grade }} 级</span>
              </div>
              <button
                v-if="!isClassSelected(c.id)"
                type="button"
                class="ml-2 shrink-0 app-btn app-btn-primary app-btn-xs"
                @click="addToSelection(c)"
              >
                + 添加
              </button>
              <button
                v-else
                type="button"
                class="ml-2 shrink-0 rounded border border-slate-300 px-2.5 py-0.5 text-xs text-slate-600 hover:bg-red-50 hover:text-red-600 hover:border-red-300"
                @click="removeFromSelection(c.id)"
              >
                移除
              </button>
            </div>
          </div>
        </div>
      </section>

      <div v-if="submitError" class="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-center text-sm text-red-700">{{ submitError }}</div>
      <div class="flex flex-wrap gap-3 border-t border-slate-100 pt-5">
        <button type="submit" class="app-btn app-btn-primary disabled:opacity-50" :disabled="submitting">
          {{ submitting ? '提交中…' : (isEdit ? '保存' : '创建') }}
        </button>
        <router-link :to="{ name: 'Users' }" class="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">取消</router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
/**
 * 用户新建/编辑表单。
 * 非学生角色的「负责班级」改为可视化选择器：按院系/专业/年级筛选候选班级，点击添加，
 * 已选以 chips 显示可单独移除，跨专业跨年级添加互不干扰。
 * 保存后通过 userListStore 记录 lastEditedId 并恢复列表页状态。
 */
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/axios'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { getUser, createUser, updateUser, getRoles } from '@/api/users'
import { useUserListStore } from '@/stores/userList'

const route = useRoute()
const router = useRouter()
const userListStore = useUserListStore()

const isEdit = computed(() => !!route.params.id)
const userId = computed(() => (route.params.id ? Number(route.params.id) : null))

const showPassword = ref(false)
const loadError = ref('')
const submitError = ref('')
const submitting = ref(false)

const form = ref({
  username: '',
  password: '',
  email: '',
  name: '',
  phone: '',
  gender: '',
  student_no: '',
  department: '',
  major: '',
  grade: '',
  class_obj: '',
  is_active: true,
  primary_role_id: '',
})

// ─── 非学生：已选负责班级（完整对象数组，提交时取 id） ─────────────
const selectedClasses = ref([])

// ─── 负责班级候选选择器独立过滤状态 ────────────────────────────────
const pickerDept = ref('')
const pickerMajor = ref('')
const pickerGrade = ref('')
const pickerMajorList = ref([])
const pickerClassList = ref([])
const pickerLoading = ref(false)

/** 候选班级年级选项（从 pickerClassList 中取不重复年级，或从 pickerMajorList 取 grades） */
const pickerGradeOptions = computed(() => {
  if (pickerMajor.value) {
    const major = pickerMajorList.value.find((m) => String(m.id) === String(pickerMajor.value))
    if (major?.grades?.length) return [...major.grades].sort()
  }
  const set = new Set(pickerClassList.value.map((c) => c.grade).filter(Boolean))
  return [...set].sort()
})

// ─── 学生所在班级相关过滤 ────────────────────────────────────────────
const formMajorList = ref([])
const formClassList = ref([])
const roleList = ref([])
const departmentTree = ref([])

/**
 * 年级选项：优先用选中专业的 grades，否则从现有班级列表取不重复 grade。
 */
const formGradeOptions = computed(() => {
  if (form.value.major) {
    const major = formMajorList.value.find((m) => String(m.id) === String(form.value.major))
    if (major?.grades?.length) return [...major.grades].sort()
  }
  const set = new Set(formClassList.value.map((c) => c.grade).filter(Boolean))
  return [...set].sort()
})

/** @returns {boolean} 学生(level=0)或学生助理(level=1)均不显示负责班级选择器 */
const isStudentRole = computed(() => {
  if (!form.value.primary_role_id) return false
  const r = roleList.value.find((x) => x.id === form.value.primary_role_id)
  return r ? r.level < 2 : false
})

const assignableRoles = computed(() => roleList.value.filter((r) => (r.level ?? -1) < 5))

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

// ─── 学生所在班级筛选级联 ─────────────────────────────────────────────

function onDepartmentChange() {
  form.value.major = ''
  form.value.grade = ''
  form.value.class_obj = ''
  loadFormMajors()
  loadFormClasses()
  // 非学生：院系变更时自动同步候选选择器的院系筛选，免去重复切换
  if (!isStudentRole.value) {
    pickerDept.value = form.value.department || ''
    onPickerDeptChange()
  }
}

function onMajorChange() {
  form.value.grade = ''
  form.value.class_obj = ''
  loadFormClasses()
}

function onGradeChange() {
  form.value.class_obj = ''
  loadFormClasses()
}

async function loadFormMajors() {
  try {
    const params = {}
    if (form.value.department) params.department = form.value.department
    const { data } = await api.get('/majors/', { params })
    formMajorList.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    formMajorList.value = []
  }
}

async function loadFormClasses() {
  try {
    const params = {}
    if (form.value.department) params.department = form.value.department
    if (form.value.major) params.major = form.value.major
    if (form.value.grade) params.grade = form.value.grade
    const { data } = await api.get('/classes/', { params })
    formClassList.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    formClassList.value = []
  }
}

async function loadDepartments() {
  try {
    const { data } = await api.get('/departments/', { params: { tree: 1 } })
    departmentTree.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    departmentTree.value = []
  }
}

// ─── 负责班级候选选择器逻辑 ───────────────────────────────────────────

async function onPickerDeptChange() {
  pickerMajor.value = ''
  pickerGrade.value = ''
  pickerMajorList.value = []
  if (pickerDept.value) {
    try {
      const { data } = await api.get('/majors/', { params: { department: pickerDept.value } })
      pickerMajorList.value = Array.isArray(data) ? data : (data?.results ?? [])
    } catch {
      pickerMajorList.value = []
    }
  }
  loadPickerClasses()
}

function onPickerMajorChange() {
  pickerGrade.value = ''
  loadPickerClasses()
}

async function loadPickerClasses() {
  pickerLoading.value = true
  try {
    const params = {}
    if (pickerDept.value) params.department = pickerDept.value
    if (pickerMajor.value) params.major = pickerMajor.value
    if (pickerGrade.value) params.grade = pickerGrade.value
    const { data } = await api.get('/classes/', { params })
    pickerClassList.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch {
    pickerClassList.value = []
  } finally {
    pickerLoading.value = false
  }
}

/**
 * 某班级是否已在选中列表中。
 * @param {number} classId
 */
function isClassSelected(classId) {
  return selectedClasses.value.some((c) => c.id === classId)
}

/**
 * 将班级加入已选列表（避免重复）。
 * @param {Object} cls - 完整班级对象
 */
function addToSelection(cls) {
  if (!isClassSelected(cls.id)) {
    selectedClasses.value.push(cls)
  }
}

/**
 * 从已选列表移除某班级。
 * @param {number} classId
 */
function removeFromSelection(classId) {
  selectedClasses.value = selectedClasses.value.filter((c) => c.id !== classId)
}

/** 将当前筛选结果中所有未选中的班级批量加入已选列表（跨专业/跨年级批量操作）。 */
function addAllPickerClasses() {
  for (const cls of pickerClassList.value) {
    addToSelection(cls)
  }
}

/**
 * 编辑模式初始化已选班级：拉取全部班级再按 ID 过滤（班级数量有限，一次请求即可）。
 * @param {number[]} ids
 */
async function initSelectedClasses(ids) {
  if (!ids?.length) {
    selectedClasses.value = []
    return
  }
  try {
    const { data } = await api.get('/classes/')
    const all = Array.isArray(data) ? data : (data?.results ?? [])
    selectedClasses.value = all.filter((c) => ids.includes(c.id))
  } catch {
    selectedClasses.value = []
  }
}

// ─── 加载用户详情（编辑回填） ────────────────────────────────────────

async function loadUserDetail() {
  if (!userId.value) return
  loadError.value = ''
  try {
    const user = await getUser(userId.value)
    const roles = (user.user_roles || []).map((ur) => ur.role).filter(Boolean)
    const topRole = roles.length
      ? roles.reduce((a, b) => ((b.level ?? 0) > (a.level ?? 0) ? b : a))
      : null
    form.value = {
      username: user.username ?? '',
      password: '',
      email: user.email ?? '',
      name: user.name ?? '',
      phone: user.phone ?? '',
      gender: user.gender ?? '',
      student_no: user.student_no || user.employee_no || '',
      department: user.department ?? '',
      major: user.class_major ?? '',
      grade: user.class_grade ?? '',
      class_obj: user.class_obj ?? '',
      is_active: user.is_active ?? true,
      primary_role_id: topRole ? topRole.id : '',
    }
    await loadFormMajors()
    await loadFormClasses()
    // 初始化非学生负责班级
    const responsibleIds = Array.isArray(user.responsible_class_ids) ? user.responsible_class_ids : []
    await initSelectedClasses(responsibleIds)
    // 初始化候选选择器班级列表（不过滤，显示全部）
    await loadPickerClasses()
    // 进入编辑页即标记「当前处理的用户」，这样无论保存、取消或点击返回，回到列表时都会高亮该行
    userListStore.setLastEdited(userId.value)
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? '加载用户详情失败'
  }
}

function parseApiError(err) {
  const data = err.response?.data
  if (data == null) return '提交失败，请重试'
  if (typeof data === 'string') return data
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) return data.detail[0] ?? '提交失败，请重试'
  for (const key of Object.keys(data)) {
    if (key === 'detail') continue
    const val = data[key]
    const msg = Array.isArray(val) ? val[0] : typeof val === 'string' ? val : null
    if (msg) return msg
  }
  return '提交失败，请重试'
}

// ─── 提交 ──────────────────────────────────────────────────────────────

async function submit() {
  submitError.value = ''
  submitting.value = true
  try {
    const payload = {
      username: form.value.username.trim(),
      email: form.value.email?.trim() || undefined,
      name: form.value.name?.trim() || undefined,
      phone: form.value.phone?.trim() || undefined,
      gender: form.value.gender || '',
      student_no: form.value.student_no?.trim() || undefined,
      employee_no: form.value.employee_no?.trim() || undefined,
      department: form.value.department || null,
      class_obj: isStudentRole.value ? (form.value.class_obj || null) : null,
      is_active: form.value.is_active,
      role_ids: form.value.primary_role_id ? [form.value.primary_role_id] : [],
      responsible_class_ids: isStudentRole.value
        ? []
        : selectedClasses.value.map((c) => c.id),
    }
    if (form.value.password?.trim()) payload.password = form.value.password.trim()

    if (isEdit.value) {
      await updateUser(userId.value, payload)
      userListStore.setLastEdited(userId.value)
      router.push({ name: 'Users' })
    } else {
      if (!payload.password) {
        submitError.value = '新建用户请填写密码'
        submitting.value = false
        return
      }
      const created = await createUser(payload)
      userListStore.setLastEdited(created?.id ?? null)
      router.push({ name: 'Users' })
    }
  } catch (e) {
    submitError.value = parseApiError(e)
  } finally {
    submitting.value = false
  }
}

// ─── Watchers ──────────────────────────────────────────────────────────

watch(
  () => route.params.id,
  (id) => { if (id) loadUserDetail() },
  { immediate: true }
)

watch(
  () => form.value.primary_role_id,
  (newId) => {
    if (!newId) return
    const r = roleList.value.find((x) => x.id === newId)
    if ((r?.level ?? -1) === 0) {
      selectedClasses.value = []
    } else {
      form.value.class_obj = ''
      form.value.major = ''
      form.value.grade = ''
      // 切换为非学生角色时，将用户已选院系同步到候选选择器，方便快速找班
      if (form.value.department) {
        pickerDept.value = form.value.department
        onPickerDeptChange()
      }
    }
  }
)

async function loadRoles() {
  try {
    roleList.value = await getRoles()
  } catch {
    roleList.value = []
  }
}

onMounted(async () => {
  await loadDepartments()
  await loadRoles()
  if (userId.value) {
    await loadUserDetail()
  } else {
    loadFormMajors()
    loadFormClasses()
    loadPickerClasses()
  }
})

useRealtimeRefresh(['department', 'major', 'class'], () => {
  loadDepartments()
  loadFormMajors()
  loadFormClasses()
  loadPickerClasses()
})
</script>
