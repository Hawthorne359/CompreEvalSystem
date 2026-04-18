<template>
  <div class="rounded-xl border border-slate-200 bg-white">
    <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3">
      <h3 class="text-sm font-semibold text-slate-800">{{ assistantLabel }}管理</h3>
      <button
        type="button"
        class="text-xs text-brand-600 hover:text-brand-700"
        @click="showAssignPanel = !showAssignPanel"
      >
        {{ showAssignPanel ? '收起' : `+ 指派${assistantLabel}` }}
      </button>
    </div>

    <!-- 班级选择 -->
    <div class="border-b border-slate-100 px-4 py-3">
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <span class="whitespace-nowrap">选择班级：</span>
        <select
          v-model="selectedClassId"
          class="app-select flex-1"
          @change="onClassChange"
        >
          <option value="">-- 请选择班级 --</option>
          <option
            v-for="cls in responsibleClasses"
            :key="cls.id"
            :value="cls.id"
          >
            {{ cls.name }}（{{ cls.grade }}级）
          </option>
        </select>
      </label>
    </div>

    <!-- 指派面板 -->
    <div v-if="showAssignPanel && selectedClassId" class="border-b border-slate-100 bg-slate-50 px-4 py-3">
      <p class="mb-2 text-xs font-medium text-slate-500">从班级学生中选择指派为{{ assistantLabel }}：</p>
      <div class="flex gap-2">
        <select v-model="assignStudentId" class="app-select flex-1 text-sm">
          <option value="">-- 选择学生 --</option>
          <option
            v-for="stu in classStudents"
            :key="stu.id"
            :value="stu.id"
            :disabled="isAlreadyAssistant(stu.id)"
          >
            {{ stu.name || stu.username }}（{{ stu.student_no || stu.username }}）
            {{ isAlreadyAssistant(stu.id) ? `（已是${assistantLabel}）` : '' }}
          </option>
        </select>
        <button
          type="button"
          class="whitespace-nowrap rounded bg-brand-500 px-3 py-1.5 text-xs text-white hover:bg-brand-600 disabled:opacity-50"
          :disabled="!assignStudentId || assigning"
          @click="doAssign"
        >
          {{ assigning ? '指派中…' : '确认指派' }}
        </button>
      </div>
      <p v-if="assignError" class="mt-1 text-xs text-red-600">{{ assignError }}</p>
      <p v-if="assignSuccess" class="mt-1 text-xs text-green-600">{{ assignSuccess }}</p>
    </div>

    <!-- 助理列表 -->
    <div class="px-4 py-3">
      <div v-if="loadingAssistants" class="py-4 text-center text-xs text-slate-400">加载中…</div>
      <div v-else-if="!selectedClassId" class="py-4 text-center text-xs text-slate-400">
        请先选择班级
      </div>
      <div v-else-if="assistants.length === 0" class="py-4 text-center text-xs text-slate-400">
        该班级暂无{{ assistantLabel }}
      </div>
      <ul v-else class="divide-y divide-slate-100">
        <li
          v-for="stu in assistants"
          :key="stu.id"
          class="flex items-center justify-between py-2"
        >
          <div>
            <span class="text-sm text-slate-800">{{ stu.name || stu.username }}</span>
            <span class="ml-2 text-xs text-slate-400">{{ stu.student_no || '' }}</span>
          </div>
          <button
            type="button"
            class="rounded border border-red-300 px-2 py-0.5 text-xs text-red-600 hover:bg-red-50"
            :disabled="revoking === stu.id"
            @click="doRevoke(stu)"
          >
            {{ revoking === stu.id ? '撤销中…' : '撤销' }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
/**
 * 辅导员管理学生助理组件。
 * 支持：选择管辖班级、查看当前助理列表、指派/撤销助理。
 * @props {Array} responsibleClasses - 辅导员管辖的班级列表 [{ id, name, grade }]
 * @props {Array} classStudents - 当前选中班级的学生列表
 */
import { ref, computed } from 'vue'
import { getAssistantList, assignAssistant, revokeAssistant } from '@/api/review'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { useRoleMetaStore } from '@/stores/roles'
import { openAlert } from '@/utils/dialog'

const roleMeta = useRoleMetaStore()
const assistantLabel = computed(() => roleMeta.nameByLevel(1))

const props = defineProps({
  /** 辅导员负责的班级列表 */
  responsibleClasses: {
    type: Array,
    default: () => [],
  },
  /** 当前选中班级的所有学生 */
  classStudents: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['class-change'])

const selectedClassId = ref('')
const showAssignPanel = ref(false)
const assistants = ref([])
const loadingAssistants = ref(false)

const assignStudentId = ref('')
const assigning = ref(false)
const assignError = ref('')
const assignSuccess = ref('')

const revoking = ref(null)

/**
 * 判断某学生是否已是该班级助理
 * @param {number} studentId
 * @returns {boolean}
 */
function isAlreadyAssistant(studentId) {
  return assistants.value.some((a) => a.id === studentId)
}

/** 班级切换时加载助理列表并通知父组件 */
async function onClassChange() {
  assignStudentId.value = ''
  assignError.value = ''
  assignSuccess.value = ''
  emit('class-change', selectedClassId.value)
  if (!selectedClassId.value) {
    assistants.value = []
    return
  }
  await loadAssistants()
}

/** 加载指定班级的助理列表 */
async function loadAssistants() {
  if (!selectedClassId.value) return
  loadingAssistants.value = true
  try {
    const res = await getAssistantList(selectedClassId.value)
    assistants.value = res.assistants ?? []
  } catch {
    assistants.value = []
  } finally {
    loadingAssistants.value = false
  }
}

/** 指派学生为助理 */
async function doAssign() {
  if (!assignStudentId.value || !selectedClassId.value) return
  assigning.value = true
  assignError.value = ''
  assignSuccess.value = ''
  try {
    await assignAssistant({
      student_id: assignStudentId.value,
      class_id: selectedClassId.value,
    })
    assignSuccess.value = '指派成功！'
    assignStudentId.value = ''
    await loadAssistants()
  } catch (e) {
    assignError.value = e.response?.data?.detail ?? '指派失败，请重试'
  } finally {
    assigning.value = false
  }
}

/**
 * 撤销某学生的助理身份
 * @param {{ id: number, name: string, username: string }} stu
 */
async function doRevoke(stu) {
  if (!selectedClassId.value) return
  revoking.value = stu.id
  try {
    await revokeAssistant({
      student_id: stu.id,
      class_id: selectedClassId.value,
    })
    await loadAssistants()
  } catch (e) {
    await openAlert({
      title: '撤销失败',
      message: e.response?.data?.detail ?? '撤销失败',
      danger: true,
    })
  } finally {
    revoking.value = null
  }
}

useRealtimeRefresh(['user', 'review_assignment'], () => {
  if (selectedClassId.value) loadAssistants()
})
</script>
