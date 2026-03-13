<template>
  <nav
    class="mobile-tab-bar md:hidden"
  >
    <router-link
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.to"
      class="tab-item"
      :class="{ active: isActive(tab.match) }"
    >
      <span v-if="isActive(tab.match)" class="tab-indicator" />
      <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <template v-if="tab.icon === 'home'">
          <path d="M3 10.5L12 3l9 7.5" />
          <path d="M5 9.5V19a1 1 0 001 1h3.5v-5a1.5 1.5 0 013 0v5H16a1 1 0 001-1V9.5" />
        </template>
        <template v-else-if="tab.icon === 'task'">
          <rect x="4" y="3" width="16" height="18" rx="2" />
          <path d="M9 7h6M9 11h6M9 15h4" />
        </template>
        <template v-else-if="tab.icon === 'appeal'">
          <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
        </template>
        <template v-else-if="tab.icon === 'report'">
          <rect x="3" y="12" width="4" height="8" rx="0.5" />
          <rect x="10" y="7" width="4" height="13" rx="0.5" />
          <rect x="17" y="3" width="4" height="17" rx="0.5" />
        </template>
        <template v-else-if="tab.icon === 'profile'">
          <circle cx="12" cy="8" r="4" />
          <path d="M5.5 21a6.5 6.5 0 0113 0" />
        </template>
      </svg>
      <span class="tab-label">{{ tab.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
/**
 * 移动端底部 Tab 导航栏。
 * 根据当前用户角色等级动态渲染 5 个 Tab，仅在 < 768px 屏幕显示。
 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ROLE_LEVEL_STUDENT, ROLE_LEVEL_ASSISTANT } from '@/constants/roles'

const route = useRoute()
const auth = useAuthStore()

const user = computed(() => auth.user)

/**
 * 根据角色等级构建 5 个 Tab 项。
 * Tab 2 因角色而异：学生→测评任务、助理→评分任务、辅导员+→审核。
 * @returns {Array<{key:string, to:object, label:string, icon:string, match:string}>}
 */
const tabs = computed(() => {
  const level = user.value?.current_role?.level ?? -1

  /** @type {{key:string, to:object, label:string, icon:string, match:string}} */
  let taskTab
  if (level <= ROLE_LEVEL_STUDENT) {
    taskTab = { key: 'submissions', to: { name: 'Submissions' }, label: '测评', icon: 'task', match: '/submissions' }
  } else if (level === ROLE_LEVEL_ASSISTANT) {
    taskTab = { key: 'assistant', to: { name: 'AssistantTasks' }, label: '评分', icon: 'task', match: '/assistant-tasks' }
  } else {
    taskTab = { key: 'review', to: { name: 'Review' }, label: '审核', icon: 'task', match: '/review' }
  }

  return [
    { key: 'home', to: { name: 'Dashboard' }, label: '首页', icon: 'home', match: '/home' },
    taskTab,
    { key: 'appeals', to: { name: 'Appeals' }, label: '申诉', icon: 'appeal', match: '/appeals' },
    { key: 'report', to: { name: 'Report' }, label: '报表', icon: 'report', match: '/report' },
    { key: 'profile', to: { name: 'Profile' }, label: '我的', icon: 'profile', match: '/profile' },
  ]
})

/**
 * 判断当前路由是否匹配 Tab 的 match 前缀。
 * @param {string} matchPath
 * @returns {boolean}
 */
function isActive(matchPath) {
  if (matchPath === '/home') return route.path === '/home' || route.path === '/'
  return route.path.startsWith(matchPath)
}
</script>
