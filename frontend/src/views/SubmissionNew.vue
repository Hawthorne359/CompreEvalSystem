<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <div class="flex items-center gap-2">
      <router-link :to="{ name: 'Submissions' }" class="text-slate-600 hover:text-slate-900">进行中的测评任务</router-link>
      <span class="text-slate-400">/</span>
      <h2 class="text-xl font-semibold text-slate-800">新建提交</h2>
    </div>

    <form class="space-y-6 rounded border border-slate-200 bg-white p-6" @submit.prevent="onSubmit">
      <p v-if="submitError" class="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{{ submitError }}</p>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">选择项目 <span class="text-red-500">*</span></label>
        <select
          v-model="form.project"
          required
          class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
          @change="onProjectChange"
        >
          <option value="">请选择项目</option>
          <option v-for="p in projectOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <p v-if="!projectOptions.length && !loadingProjects" class="mt-1 text-xs text-slate-500">暂无可选项目</p>
      </div>

      <!-- 学生自评分数（结构化输入，仅显示 score_source='self' 的叶子指标） -->
      <div v-if="selfIndicators.length">
        <p class="mb-2 text-sm font-medium text-slate-700">自评分数</p>
        <p class="mb-3 text-xs text-slate-500">以下指标需要您自行填报分数，{{ counselorLabel }}将在审核时确认。</p>
        <div class="space-y-2">
          <div
            v-for="ind in selfIndicators"
            :key="ind.id"
            class="flex items-center gap-3 rounded border border-slate-200 bg-purple-50 px-3 py-2"
          >
            <span class="flex-1 text-sm text-slate-800">
              {{ ind.parentName ? ind.parentName + ' › ' : '' }}{{ ind.name }}
            </span>
            <span class="text-xs text-slate-400">
              <template v-if="ind.max_score != null">满分 {{ ind.max_score }}</template>
              <template v-else>无上限</template>
            </span>
            <span
              v-if="ind.parent_agg_formula === 'sum_capped'"
              class="text-xs"
              :class="(sumCappedRemainingMap[ind.parent_indicator_id] ?? 0) <= 0 ? 'text-red-500' : 'text-amber-600'"
            >
              可用 {{ sumCappedRemainingMap[ind.parent_indicator_id] ?? ind.parent_max_score }} 分
            </span>
            <input
              v-model.number="selfScoreInputs[ind.id]"
              type="number"
              :min="0"
              :max="ind.parent_agg_formula === 'sum_capped'
                ? (sumCappedRemainingMap[ind.parent_indicator_id] ?? ind.parent_max_score)
                : (ind.max_score != null ? ind.max_score : undefined)"
              :step="0.01"
              placeholder="填写分数"
              class="w-28 rounded border border-slate-300 px-2.5 py-1.5 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>
        </div>
      </div>
      <div v-else-if="form.project && !loadingIndicators" class="rounded border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-500">
        该项目无需学生自评，直接创建草稿即可。
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">备注</label>
        <textarea
          v-model="form.remark"
          rows="2"
          class="w-full rounded border border-slate-300 px-3 py-2 text-slate-800 focus:border-brand-500 focus:outline-none"
          placeholder="选填"
        />
      </div>

      <div class="flex gap-3">
        <button
          type="submit"
          class="app-btn app-btn-primary disabled:opacity-50"
          :disabled="submitLoading"
        >
          {{ submitLoading ? '创建中…' : '创建草稿' }}
        </button>
        <router-link
          :to="{ name: 'Submissions' }"
          class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
        >
          取消
        </router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
/**
 * 新建提交：选择项目、自评分数（结构化输入，仅含 score_source='self' 的指标）、备注，
 * 创建草稿后跳转详情页继续上传佐证与正式提交。
 * 接口：POST /api/v1/submissions/
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { createSubmission } from '@/api/submissions'
import { getSeasons, getSeasonProjects, getIndicatorTree } from '@/api/eval'
import { useRoleMetaStore } from '@/stores/roles'

const roleMeta = useRoleMetaStore()
const counselorLabel = computed(() => roleMeta.nameByLevel(2))

const router = useRouter()
const submitLoading = ref(false)
const submitError = ref('')
const loadingProjects = ref(false)
const loadingIndicators = ref(false)
const projectOptions = ref([])
const indicatorTree = ref([])
const selfScoreInputs = reactive({})  // { [indicator_id]: score }

const form = reactive({
  project: '',
  remark: '',
})

/** 从树中提取 score_source='self' 的叶子指标，附加 parentName 及父项聚合信息 */
const selfIndicators = computed(() => {
  const result = []
  for (const top of indicatorTree.value) {
    if (top.children && top.children.length > 0) {
      for (const child of top.children) {
        if (child.score_source === 'self') {
          result.push({
            ...child,
            parentName: top.name,
            parent_indicator_id: top.id,
            parent_agg_formula: top.agg_formula,
            parent_max_score: top.max_score,
          })
        }
      }
    } else if (top.score_source === 'self') {
      result.push({ ...top, parentName: null, parent_indicator_id: null, parent_agg_formula: null, parent_max_score: null })
    }
  }
  return result
})

/**
 * 对父项 agg_formula='sum_capped' 的指标组，计算剩余可用分。
 * 返回 { [parent_indicator_id]: 剩余可用分 }
 */
const sumCappedRemainingMap = computed(() => {
  const result = {}
  for (const ind of selfIndicators.value) {
    if (ind.parent_agg_formula !== 'sum_capped' || !ind.parent_indicator_id) continue
    const pid = ind.parent_indicator_id
    const cap = Number(ind.parent_max_score)
    const used = selfIndicators.value
      .filter((i) => i.parent_indicator_id === pid)
      .reduce((sum, i) => sum + (Number(selfScoreInputs[i.id]) || 0), 0)
    result[pid] = Math.max(0, cap - used)
  }
  return result
})

async function loadProjects() {
  loadingProjects.value = true
  try {
    const seasons = await getSeasons()
    const all = []
    for (const s of seasons) {
      const projects = await getSeasonProjects(s.id)
      all.push(...projects.map((p) => ({ id: p.id, name: p.name })))
    }
    projectOptions.value = all
  } catch {
    projectOptions.value = []
  } finally {
    loadingProjects.value = false
  }
}

async function onProjectChange() {
  indicatorTree.value = []
  // 清空之前的自评输入
  for (const key of Object.keys(selfScoreInputs)) {
    delete selfScoreInputs[key]
  }
  if (!form.project) return
  loadingIndicators.value = true
  try {
    indicatorTree.value = await getIndicatorTree(Number(form.project))
  } catch {
    indicatorTree.value = []
  } finally {
    loadingIndicators.value = false
  }
}

async function onSubmit() {
  submitError.value = ''
  submitLoading.value = true
  try {
    // 将结构化自评输入构建为 { [indicator_id]: score } 格式
    const selfScore = {}
    for (const ind of selfIndicators.value) {
      const val = selfScoreInputs[ind.id]
      if (val != null && val !== '') {
        selfScore[ind.id] = Number(val)
      }
    }
    const body = {
      project: Number(form.project),
      self_score: selfScore,
      remark: form.remark.trim() || undefined,
    }
    const created = await createSubmission(body)
    router.push({ name: 'SubmissionDetail', params: { id: created.id } })
  } catch (e) {
    const msg = e.response?.data?.detail ?? e.response?.data?.project?.[0] ?? '创建失败'
    submitError.value = typeof msg === 'string' ? msg : JSON.stringify(msg)
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadProjects()
})

useRealtimeRefresh(['project', 'season'], loadProjects)
</script>
