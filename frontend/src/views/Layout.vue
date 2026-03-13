<template>
  <div class="layout-shell">
    <header class="layout-header border-b border-slate-200/70 bg-white/80 backdrop-blur-xl">
      <div class="mx-auto flex h-14 max-w-6xl items-center justify-between px-3 md:px-4">
        <div class="flex items-center gap-2">
          <!-- 移动端：学校 Logo 按钮（点击展开快捷入口面板） -->
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-full transition-transform duration-150 active:scale-90 md:hidden"
            @click="quickPanelOpen = !quickPanelOpen"
          >
            <img src="@/assets/logo.svg" alt="校徽" class="h-7 w-7 rounded-full object-contain" />
          </button>
          <div class="flex flex-col">
            <h1 class="text-base font-semibold text-slate-800 md:text-lg">校园综合测评管理系统</h1>
            <span class="text-[10px] leading-tight text-slate-300 md:hidden">点击图标展开快捷窗口</span>
          </div>
        </div>
        <!-- 移动端：系统管理入口（仅管理员可见） -->
        <router-link
          v-if="isAdmin"
          :to="{ name: 'Admin' }"
          class="flex flex-col items-center justify-center gap-0.5 text-slate-500 hover:text-slate-700 transition-all duration-150 active:scale-90 md:hidden -my-1"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" /></svg>
          <span class="text-[10px] leading-none font-medium">管理</span>
        </router-link>
        <!-- 桌面端：角色切换 + 用户下拉菜单 -->
        <div class="hidden items-center gap-3 md:flex">
          <template v-if="hasMultipleRoles">
            <div class="relative" data-role-dropdown>
              <button
                type="button"
                class="flex items-center gap-1 rounded bg-slate-200 px-2 py-1 text-xs text-slate-700 hover:bg-slate-300"
                @click="roleDropdownOpen = !roleDropdownOpen"
              >
                {{ user?.current_role?.name ?? '选择角色' }}
                <span class="text-[10px]">▼</span>
              </button>
              <div
                v-if="roleDropdownOpen"
                class="absolute right-0 top-full z-10 mt-1 min-w-[120px] rounded border border-slate-200 bg-white py-1 shadow"
              >
                <button
                  v-for="r in roleList"
                  :key="r.id"
                  type="button"
                  class="w-full px-3 py-1.5 text-left text-sm hover:bg-slate-100"
                  :class="user?.current_role?.id === r.id ? 'bg-slate-100 font-medium' : ''"
                  @click="onSelectRole(r)"
                >
                  {{ r.name }}
                </button>
              </div>
            </div>
          </template>
          <span v-else-if="currentRoleName" class="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{{ currentRoleName }}</span>
          <p v-if="roleError" class="text-xs text-red-600">{{ roleError }}</p>
          <!-- 用户下拉菜单 -->
          <div class="relative" data-user-dropdown>
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm text-slate-700 hover:bg-slate-100 transition-colors"
              @click="userDropdownOpen = !userDropdownOpen"
            >
              <span class="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold" :class="[avatarColors.bg, avatarColors.text]">{{ avatarInitial }}</span>
              <span>{{ displayName }}</span>
              <svg class="h-3.5 w-3.5 text-slate-400 transition-transform" :class="userDropdownOpen ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" /></svg>
            </button>
            <Transition name="dropdown-fade">
              <div
                v-if="userDropdownOpen"
                class="absolute right-0 top-full z-10 mt-1 min-w-[160px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
              >
                <router-link
                  :to="{ name: 'Profile' }"
                  class="flex items-center gap-2 px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                  @click="userDropdownOpen = false"
                >
                  <svg class="h-4 w-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4" /><path d="M5.5 21a6.5 6.5 0 0113 0" /></svg>
                  个人中心
                </router-link>
                <button
                  type="button"
                  class="flex w-full items-center gap-2 border-t border-slate-100 px-3 py-2.5 text-sm text-red-500 hover:bg-red-50"
                  @click="userDropdownOpen = false; logout()"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><polyline points="16,17 21,12 16,7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                  退出登录
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
      <!-- 桌面端：顶部导航栏（居中 · 液态玻璃胶囊 · 滑块动画） -->
      <nav class="mx-auto hidden max-w-6xl justify-center px-4 pb-2 pt-1 md:flex">
        <div ref="topNavRef" class="liquid-glass-nav">
          <div class="liquid-glass-slider" :style="topSliderStyle"></div>
          <router-link
            v-for="(item, idx) in navItems"
            :key="item.path"
            :ref="el => setTopPillRef(el, idx)"
            :to="item.to"
            class="liquid-glass-pill"
            :class="isActive(item.path) ? 'is-sliding-active' : ''"
          >
            <svg class="pill-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <template v-if="item.icon === 'home'">
                <path d="M3 10.5L12 3l9 7.5" /><path d="M5 9.5V19a1 1 0 001 1h3.5v-5a1.5 1.5 0 013 0v5H16a1 1 0 001-1V9.5" />
              </template>
              <template v-else-if="item.icon === 'task'">
                <rect x="4" y="3" width="16" height="18" rx="2" /><path d="M9 7h6M9 11h6M9 15h4" />
              </template>
              <template v-else-if="item.icon === 'review'">
                <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </template>
              <template v-else-if="item.icon === 'appeal'">
                <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
              </template>
              <template v-else-if="item.icon === 'report'">
                <rect x="3" y="12" width="4" height="8" rx="0.5" /><rect x="10" y="7" width="4" height="13" rx="0.5" /><rect x="17" y="3" width="4" height="17" rx="0.5" />
              </template>
              <template v-else-if="item.icon === 'log'">
                <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" />
              </template>
              <template v-else-if="item.icon === 'admin'">
                <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
              </template>
            </svg>
            {{ item.label }}
          </router-link>
        </div>
      </nav>

      <!-- 密码校验弹窗（桌面端角色切换） -->
      <Teleport to="body">
        <div
          v-if="showPasswordModal"
          class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-3 md:p-4"
          @click.self="cancelPasswordModal"
        >
          <div class="app-modal w-full max-w-md p-5 shadow-2xl md:p-6">
            <h3 class="text-base font-medium text-slate-800">切换到「{{ pendingRole?.name }}」角色</h3>
            <p class="mt-1 text-sm text-slate-500">目标角色权限较高，请输入登录密码以验证身份</p>
            <input
              v-model="switchPassword"
              type="password"
              class="mt-3 w-full rounded border border-slate-300 px-3 py-2 text-slate-800"
              placeholder="密码"
              @keydown.enter="confirmSwitchRole"
            />
            <p v-if="passwordModalError" class="mt-2 text-sm text-red-600">{{ passwordModalError }}</p>
            <div class="mt-4 flex justify-end gap-2">
              <button
                type="button"
                class="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                @click="cancelPasswordModal"
              >
                取消
              </button>
              <button
                type="button"
                class="rounded bg-brand-500 px-3 py-1.5 text-sm text-white hover:bg-brand-600"
                :disabled="switchRoleLoading"
                @click="confirmSwitchRole"
              >
                {{ switchRoleLoading ? '验证中…' : '确认' }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </header>

    <!-- 移动端：快捷入口下拉面板 -->
    <Transition name="quick-panel">
      <div
        v-if="quickPanelOpen"
        class="quick-panel md:hidden"
        @click.self="quickPanelOpen = false"
      >
        <div class="quick-panel__body">
          <div class="quick-grid">
            <router-link
              v-for="item in quickShortcuts"
              :key="item.label"
              :to="item.to"
              class="quick-grid-item"
              @click="quickPanelOpen = false"
            >
              <div class="quick-grid-item__icon" :class="item.iconClass">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="item.svgPath" />
              </div>
              <span class="quick-grid-item__label">{{ item.label }}</span>
            </router-link>
          </div>
        </div>
      </div>
    </Transition>

    <div class="layout-body md:mx-auto md:max-w-[1260px] md:w-full md:gap-1.5">
      <!-- 桌面端：快捷入口 Dock 栏（左/右由 CSS order 控制） -->
      <aside
        v-if="quickShortcuts.length"
        class="quick-sidebar hidden md:flex"
        :style="{ order: sidebarSide === 'left' ? -1 : 1 }"
      >
        <div
          class="quick-sidebar__inner"
          :style="{ top: sidebarTopVh + 'vh' }"
        >
          <span class="quick-sidebar__title">快捷入口</span>
          <router-link
            v-for="item in quickShortcuts"
            :key="'sb-'+item.label"
            :to="item.to"
            class="quick-sidebar__item"
          >
            <div class="quick-sidebar__icon" :class="item.iconClass">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="item.svgPath" />
            </div>
            <span class="quick-sidebar__label">{{ item.label }}</span>
          </router-link>
          <button type="button" class="quick-sidebar__toggle" :title="sidebarSide === 'right' ? '移到左侧' : '移到右侧'" @click="toggleSidebarSide">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline :points="sidebarSide === 'right' ? '15 18 9 12 15 6' : '9 18 15 12 9 6'" />
            </svg>
          </button>
          <div
            class="quick-sidebar__drag"
            title="拖拽上下移动"
            @mousedown.prevent="onDockDragStart"
            @touchstart.prevent="onDockDragStart"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><circle cx="8" cy="8" r="1.5"/><circle cx="16" cy="8" r="1.5"/><circle cx="8" cy="12" r="1.5"/><circle cx="16" cy="12" r="1.5"/><circle cx="8" cy="16" r="1.5"/><circle cx="16" cy="16" r="1.5"/></svg>
          </div>
        </div>
      </aside>

      <main class="layout-main px-3 py-4 md:px-5 md:py-6 md:pb-6">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 移动端底部 Tab 导航栏 -->
    <MobileTabBar />
  </div>
</template>

<script setup>
/**
 * 主布局：顶栏（标题、用户名、角色切换、退出）、导航、主内容区。
 * 移动端使用底部 Tab 导航栏替代汉堡菜单，桌面端保持顶部导航不变。
 */
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoleMetaStore } from '@/stores/roles'
import MobileTabBar from '@/components/MobileTabBar.vue'
import { getAvatarInitial, getAvatarColor } from '@/composables/useAvatar'
import {
  ROLE_LEVEL_STUDENT,
  ROLE_LEVEL_ASSISTANT,
  ROLE_LEVEL_COUNSELOR,
  ROLE_LEVEL_DIRECTOR,
  ROLE_LEVEL_SUPERADMIN,
} from '@/constants/roles'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const user = computed(() => auth.user)

/** 显示姓名：name 字段，无则回退到 username */
const displayName = computed(() => {
  const u = user.value
  if (!u) return ''
  return u.name || u.username || ''
})

const avatarInitial = computed(() => getAvatarInitial(displayName.value))
const avatarColors = computed(() => getAvatarColor(user.value?.username))

/** @returns {boolean} 当前用户是否为最高管理角色（LV5+） */
const isAdmin = computed(() => (user.value?.current_role?.level ?? -1) >= ROLE_LEVEL_SUPERADMIN)

/**
 * 当前用户可切换的角色列表（来自 user_roles[].role）。
 * 同一 role 可能因「负责班级」产生多条 UserRole 记录，需按 role.id 去重。
 */
const roleList = computed(() => {
  const seen = new Set()
  return (user.value?.user_roles ?? [])
    .map((ur) => ur.role)
    .filter((role) => {
      if (!role || seen.has(role.id)) return false
      seen.add(role.id)
      return true
    })
    .sort((a, b) => (b.level ?? 0) - (a.level ?? 0))
})

/** 是否有多于一个角色（仅多角色时显示下拉） */
const hasMultipleRoles = computed(() => roleList.value.length > 1)

/** 当前角色名称（单角色时直接显示，不设按钮） */
const currentRoleName = computed(() => user.value?.current_role?.name ?? null)

const roleDropdownOpen = ref(false)
const userDropdownOpen = ref(false)
const quickPanelOpen = ref(false)

/** 桌面端快捷入口侧边栏：左右位置 + 垂直偏移，持久化到 localStorage */
const sidebarSide = ref(localStorage.getItem('quickSidebarSide') || 'right')
const sidebarTopVh = ref(parseFloat(localStorage.getItem('quickSidebarTopVh')) || 32)

function toggleSidebarSide() {
  sidebarSide.value = sidebarSide.value === 'right' ? 'left' : 'right'
  localStorage.setItem('quickSidebarSide', sidebarSide.value)
}

/** Dock 栏垂直拖拽 */
let _dockDragStartY = 0
let _dockDragStartVh = 0

function onDockDragStart(/** @type {MouseEvent|TouchEvent} */ e) {
  _dockDragStartY = e.clientY ?? e.touches[0].clientY
  _dockDragStartVh = sidebarTopVh.value
  document.addEventListener('mousemove', onDockDragMove)
  document.addEventListener('mouseup', onDockDragEnd)
  document.addEventListener('touchmove', onDockDragMove, { passive: false })
  document.addEventListener('touchend', onDockDragEnd)
  document.body.style.userSelect = 'none'
}

function onDockDragMove(/** @type {MouseEvent|TouchEvent} */ e) {
  e.preventDefault()
  const clientY = e.clientY ?? e.touches[0].clientY
  const deltaVh = ((clientY - _dockDragStartY) / window.innerHeight) * 100
  sidebarTopVh.value = Math.max(5, Math.min(88, _dockDragStartVh + deltaVh))
}

function onDockDragEnd() {
  document.removeEventListener('mousemove', onDockDragMove)
  document.removeEventListener('mouseup', onDockDragEnd)
  document.removeEventListener('touchmove', onDockDragMove)
  document.removeEventListener('touchend', onDockDragEnd)
  document.body.style.userSelect = ''
  localStorage.setItem('quickSidebarTopVh', sidebarTopVh.value.toFixed(1))
}
const roleError = ref('')
const showPasswordModal = ref(false)
const switchPassword = ref('')
const passwordModalError = ref('')
const switchRoleLoading = ref(false)
/** 待切换的角色（需密码验证时使用） */
const pendingRole = ref(null)

/**
 * 导航菜单按当前角色 level 动态显示（桌面端使用）。
 * LV0=学生  LV1=学生助理  LV2=评审老师（辅导员）  LV3=院系主任  LV5=超级管理员
 */
const navItems = computed(() => {
  const level = user.value?.current_role?.level ?? -1
  /** @type {Array<{ to: object, label: string, path: string, icon: string }>} */
  const items = [{ to: { name: 'Dashboard' }, label: '工作台', path: '/home', icon: 'home' }]
  if (level === ROLE_LEVEL_STUDENT) items.push({ to: { name: 'Submissions' }, label: '进行中的测评任务', path: '/submissions', icon: 'task' })
  if (level === ROLE_LEVEL_ASSISTANT) items.push({ to: { name: 'AssistantTasks' }, label: '待评分任务', path: '/assistant-tasks', icon: 'task' })
  if (level >= ROLE_LEVEL_COUNSELOR) items.push({ to: { name: 'Review' }, label: level >= ROLE_LEVEL_DIRECTOR ? '提交监控' : '审核', path: '/review', icon: 'review' })
  items.push({ to: { name: 'Appeals' }, label: '申诉', path: '/appeals', icon: 'appeal' })
  items.push({ to: { name: 'Report' }, label: '成绩报表', path: '/report', icon: 'report' })
  if (level < ROLE_LEVEL_SUPERADMIN) items.push({ to: { name: 'MyOperationLog' }, label: '我的操作记录', path: '/my-logs', icon: 'log' })
  if (level >= ROLE_LEVEL_SUPERADMIN) items.push({ to: { name: 'Admin' }, label: '系统管理', path: '/admin', icon: 'admin' })
  return items
})

/**
 * 移动端快捷入口面板按角色 level 返回不同列表。
 * @returns {Array<{to: object, label: string, svgPath: string, iconClass: string}>}
 */
const quickShortcuts = computed(() => {
  const level = user.value?.current_role?.level ?? -1
  if (level === ROLE_LEVEL_STUDENT) {
    return [
      { to: { name: 'Submissions' }, label: '我的测评', svgPath: '<rect x="4" y="3" width="16" height="18" rx="2" /><path d="M9 7h6M9 11h6M9 15h4" />', iconClass: 'bg-brand-100 text-brand-600' },
      { to: { name: 'Appeals' }, label: '发起申诉', svgPath: '<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />', iconClass: 'bg-amber-100 text-amber-600' },
      { to: { name: 'Report' }, label: '我的成绩', svgPath: '<rect x="3" y="12" width="4" height="8" rx="0.5" /><rect x="10" y="7" width="4" height="13" rx="0.5" /><rect x="17" y="3" width="4" height="17" rx="0.5" />', iconClass: 'bg-green-100 text-green-600' },
    ]
  }
  if (level === ROLE_LEVEL_ASSISTANT) {
    return [
      { to: { name: 'AssistantTasks' }, label: '待评分列表', svgPath: '<path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />', iconClass: 'bg-brand-100 text-brand-600' },
      { to: { name: 'MyOperationLog' }, label: '评分记录', svgPath: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />', iconClass: 'bg-blue-100 text-blue-600' },
      { to: { name: 'Submissions' }, label: '我的测评', svgPath: '<rect x="4" y="3" width="16" height="18" rx="2" /><path d="M9 7h6M9 11h6M9 15h4" />', iconClass: 'bg-green-100 text-green-600' },
    ]
  }
  if (level === ROLE_LEVEL_COUNSELOR) {
    return [
      { to: { name: 'Review' }, label: '审核双评', svgPath: '<path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />', iconClass: 'bg-brand-100 text-brand-600' },
      { to: { name: 'Appeals' }, label: '处理申诉', svgPath: '<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />', iconClass: 'bg-amber-100 text-amber-600' },
      { to: { name: 'Report' }, label: '班级报表', svgPath: '<rect x="3" y="12" width="4" height="8" rx="0.5" /><rect x="10" y="7" width="4" height="13" rx="0.5" /><rect x="17" y="3" width="4" height="17" rx="0.5" />', iconClass: 'bg-blue-100 text-blue-600' },
      { to: { name: 'UserImportQuick' }, label: '导入学生', svgPath: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />', iconClass: 'bg-green-100 text-green-600' },
    ]
  }
  if (level === ROLE_LEVEL_DIRECTOR) {
    return [
      { to: { name: 'Report' }, label: '全院数据', svgPath: '<rect x="3" y="12" width="4" height="8" rx="0.5" /><rect x="10" y="7" width="4" height="13" rx="0.5" /><rect x="17" y="3" width="4" height="17" rx="0.5" />', iconClass: 'bg-brand-100 text-brand-600' },
      { to: { name: 'Appeals' }, label: '处理申诉', svgPath: '<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />', iconClass: 'bg-amber-100 text-amber-600' },
      { to: { name: 'UserImportQuick' }, label: '导入用户', svgPath: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />', iconClass: 'bg-green-100 text-green-600' },
      { to: { name: 'Review' }, label: '提交监控', svgPath: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />', iconClass: 'bg-blue-100 text-blue-600' },
    ]
  }
  if (level >= ROLE_LEVEL_SUPERADMIN) {
    return [
      { to: { name: 'Users' }, label: '用户管理', svgPath: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />', iconClass: 'bg-brand-100 text-brand-600' },
      { to: { name: 'UserImport' }, label: '批量导入', svgPath: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />', iconClass: 'bg-green-100 text-green-600' },
      { to: { name: 'Seasons' }, label: '测评周期', svgPath: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />', iconClass: 'bg-blue-100 text-blue-600' },
      { to: { name: 'Organization' }, label: '组织架构', svgPath: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><line x1="19" y1="8" x2="19" y2="14" /><line x1="22" y1="11" x2="16" y2="11" />', iconClass: 'bg-purple-100 text-purple-600' },
      { to: { name: 'SystemAdmin' }, label: '系统审计', svgPath: '<circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />', iconClass: 'bg-amber-100 text-amber-600' },
      { to: { name: 'Review' }, label: '审核监控', svgPath: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />', iconClass: 'bg-cyan-100 text-cyan-600' },
      { to: { name: 'Appeals' }, label: '申诉管理', svgPath: '<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />', iconClass: 'bg-rose-100 text-rose-600' },
    ]
  }
  return []
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

/* ── 顶部导航滑块跟踪 ── */
const topNavRef = ref(null)
const topPillEls = {}
const topSliderStyle = ref({ opacity: '0' })
let topSliderInit = false

/**
 * @param {import('vue').ComponentPublicInstance|Element|null} el
 * @param {number} idx
 */
function setTopPillRef(el, idx) {
  if (el) topPillEls[idx] = el.$el || el
}

function syncTopSlider() {
  const activeIdx = navItems.value.findIndex(item => isActive(item.path))
  const el = topPillEls[activeIdx]
  if (activeIdx < 0 || !el || !topNavRef.value) return
  const style = {
    left: `${el.offsetLeft}px`,
    top: `${el.offsetTop}px`,
    width: `${el.offsetWidth}px`,
    height: `${el.offsetHeight}px`,
    opacity: '1',
  }
  if (!topSliderInit) {
    topSliderInit = true
    style.transition = 'none'
    topSliderStyle.value = style
    requestAnimationFrame(() => {
      topSliderStyle.value = { ...topSliderStyle.value, transition: '' }
    })
  } else {
    topSliderStyle.value = style
  }
}

watch(() => route.path, () => {
  quickPanelOpen.value = false
  nextTick(syncTopSlider)
})
watch(navItems, () => {
  topSliderInit = false
  nextTick(() => setTimeout(syncTopSlider, 60))
}, { flush: 'post' })

/**
 * 选择要切换的角色：目标角色 level 高于当前角色 level 时弹出密码框，否则直接切换。
 * @param {Object} role - { id, code, name, level }
 */
function onSelectRole(role) {
  roleError.value = ''
  const currentLevel = user.value?.current_role?.level ?? -1
  const targetLevel = role?.level ?? -1
  const needPassword = targetLevel > currentLevel
  if (needPassword) {
    pendingRole.value = role
    switchPassword.value = ''
    passwordModalError.value = ''
    showPasswordModal.value = true
    roleDropdownOpen.value = false
  } else {
    roleDropdownOpen.value = false
    doSwitchRole(role.id, '').catch((e) => {
      roleError.value = e.response?.data?.detail ?? '切换失败'
    })
  }
}

/** 确认切换（密码弹窗内点击确认） */
async function confirmSwitchRole() {
  if (!pendingRole.value) return
  passwordModalError.value = ''
  if (!switchPassword.value.trim()) {
    passwordModalError.value = '请输入密码后再确认'
    return
  }
  switchRoleLoading.value = true
  try {
    await doSwitchRole(pendingRole.value.id, switchPassword.value.trim())
    showPasswordModal.value = false
    pendingRole.value = null
    switchPassword.value = ''
  } catch (e) {
    passwordModalError.value = e.response?.data?.detail ?? '验证失败'
  } finally {
    switchRoleLoading.value = false
  }
}

/**
 * 调用后端切换角色并更新 store，切换成功后跳转工作台。
 * @param {number} roleId
 * @param {string} password
 */
async function doSwitchRole(roleId, password) {
  await auth.switchRole(roleId, password)
  roleError.value = ''
  router.push({ name: 'Dashboard' })
}

function cancelPasswordModal() {
  showPasswordModal.value = false
  pendingRole.value = null
  switchPassword.value = ''
  passwordModalError.value = ''
}

/** 点击页面其他区域关闭下拉菜单 */
function onDocumentClick(e) {
  const roleDropdown = document.querySelector('[data-role-dropdown]')
  if (roleDropdown && !roleDropdown.contains(e.target)) {
    roleDropdownOpen.value = false
  }
  const userDropdown = document.querySelector('[data-user-dropdown]')
  if (userDropdown && !userDropdown.contains(e.target)) {
    userDropdownOpen.value = false
  }
}

function logout() {
  auth.logout()
  router.push({ name: 'Login' })
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  nextTick(() => setTimeout(syncTopSlider, 60))
  useRoleMetaStore().ensureLoaded()
})
onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style scoped>
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity .15s ease, transform .15s ease;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

</style>
