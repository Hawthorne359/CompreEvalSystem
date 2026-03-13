<template>
  <div class="page-shell">
    <h2 class="app-page-title">系统管理</h2>

    <!-- ═══ 移动端：入口卡片菜单（仅 /admin 根路径显示） ═══ -->
    <div v-if="isAdminRoot" class="mt-4 md:hidden">
      <div class="grid grid-cols-2 gap-3">
        <router-link
          v-for="entry in adminEntries"
          :key="entry.name"
          :to="entry.to"
          class="admin-mobile-card"
        >
          <div class="admin-mobile-card__icon" :class="entry.iconBg">
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" v-html="entry.svgPath" />
          </div>
          <span class="admin-mobile-card__title">{{ entry.label }}</span>
          <span class="admin-mobile-card__desc">{{ entry.desc }}</span>
        </router-link>
      </div>
    </div>

    <!-- ═══ 移动端：子页面返回导航条 ═══ -->
    <div v-if="!isAdminRoot" class="admin-mobile-header md:hidden">
      <button type="button" class="admin-mobile-back" @click="goBackToAdmin">
        <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clip-rule="evenodd" /></svg>
        <span>系统管理</span>
      </button>
      <span class="admin-mobile-current">{{ currentSubTitle }}</span>
    </div>

    <!-- ═══ 桌面端：液态玻璃标签导航（不变） ═══ -->
    <nav class="mt-4 hidden justify-center overflow-x-auto pb-2 scrollbar-hide md:flex">
      <div ref="subNavRef" class="liquid-glass-nav">
        <div class="liquid-glass-slider" :style="sliderStyle"></div>
        <router-link
          :to="{ name: 'Seasons' }"
          :ref="el => setPillRef(el, 0)"
          class="liquid-glass-pill"
          :class="isSeasons ? 'is-sliding-active' : ''"
        >
          <svg class="admin-sub-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" /></svg>
          测评项目
        </router-link>
        <router-link
          :to="{ name: 'Organization' }"
          :ref="el => setPillRef(el, 1)"
          class="liquid-glass-pill"
          :class="isOrg ? 'is-sliding-active' : ''"
        >
          <svg class="admin-sub-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="5" rx="1" /><rect x="2" y="17" width="6" height="5" rx="1" /><rect x="16" y="17" width="6" height="5" rx="1" /><path d="M12 7v5M5 17v-3a2 2 0 012-2h10a2 2 0 012 2v3" /></svg>
          组织架构
        </router-link>
        <router-link
          :to="{ name: 'Users' }"
          :ref="el => setPillRef(el, 2)"
          class="liquid-glass-pill"
          :class="isUsers ? 'is-sliding-active' : ''"
        >
          <svg class="admin-sub-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" /></svg>
          用户管理
        </router-link>
        <router-link
          :to="{ name: 'SystemAdmin' }"
          :ref="el => setPillRef(el, 3)"
          class="liquid-glass-pill"
          :class="isSystem ? 'is-sliding-active' : ''"
        >
          <svg class="admin-sub-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></svg>
          审计与操控
        </router-link>
      </div>
    </nav>

    <!-- ═══ 子页面内容（桌面端始终显示，移动端仅非 root 时显示） ═══ -->
    <div class="mt-4" :class="{ 'hidden md:block': isAdminRoot }">
      <router-view />
    </div>
  </div>
</template>

<script setup>
/**
 * 系统管理布局。
 * 桌面端：子导航（液态玻璃滑块动画）+ 子页面出口。
 * 移动端：入口卡片菜单（/admin）或 返回导航 + 子页面。
 */
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

/** 是否停留在 admin 根路径（未进入子页面） */
const isAdminRoot = computed(() => route.path === '/admin' || route.path === '/admin/')

const flags = [
  computed(() => route.path.startsWith('/admin/seasons') || route.path.startsWith('/admin/projects')),
  computed(() => route.path.startsWith('/admin/organization')),
  computed(() => route.path.startsWith('/admin/users')),
  computed(() => route.path.startsWith('/admin/system')),
]
const isSeasons = flags[0]
const isOrg = flags[1]
const isUsers = flags[2]
const isSystem = flags[3]

/** 移动端子页面标题 */
const currentSubTitle = computed(() => {
  if (isSeasons.value) return '测评项目'
  if (isOrg.value) return '组织架构'
  if (isUsers.value) return '用户管理'
  if (isSystem.value) return '审计与操控'
  return ''
})

/**
 * 移动端管理入口卡片列表。
 * @type {Array<{name: string, to: object, label: string, desc: string, iconBg: string, svgPath: string}>}
 */
const adminEntries = [
  {
    name: 'seasons',
    to: { name: 'Seasons' },
    label: '测评项目',
    desc: '周期与项目配置',
    iconBg: 'bg-brand-100 text-brand-600',
    svgPath: '<rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" />',
  },
  {
    name: 'org',
    to: { name: 'Organization' },
    label: '组织架构',
    desc: '院系、专业与班级',
    iconBg: 'bg-blue-100 text-blue-600',
    svgPath: '<rect x="9" y="2" width="6" height="5" rx="1" /><rect x="2" y="17" width="6" height="5" rx="1" /><rect x="16" y="17" width="6" height="5" rx="1" /><path d="M12 7v5M5 17v-3a2 2 0 012-2h10a2 2 0 012 2v3" />',
  },
  {
    name: 'users',
    to: { name: 'Users' },
    label: '用户管理',
    desc: '账号与角色管理',
    iconBg: 'bg-emerald-100 text-emerald-600',
    svgPath: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />',
  },
  {
    name: 'system',
    to: { name: 'SystemAdmin' },
    label: '审计与操控',
    desc: '日志、通道与策略',
    iconBg: 'bg-amber-100 text-amber-600',
    svgPath: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" />',
  },
]

/** 返回管理入口菜单 */
function goBackToAdmin() {
  router.push({ name: 'Admin' })
}

/**
 * 桌面端：若停留在 admin 根路径则自动跳转到 Seasons。
 * 移动端停留在根路径显示卡片菜单，不跳转。
 */
onMounted(() => {
  if (isAdminRoot.value && window.innerWidth >= 768) {
    router.replace({ name: 'Seasons' })
  }
  nextTick(() => setTimeout(syncSlider, 60))
})

/* ── 滑块跟踪（桌面端） ── */
const subNavRef = ref(null)
const pillEls = {}
const sliderStyle = ref({ opacity: '0' })
let sliderInit = false

/** @param {import('vue').ComponentPublicInstance|Element|null} el */
function setPillRef(el, idx) {
  if (el) pillEls[idx] = el.$el || el
}

function activeIndex() {
  return flags.findIndex(f => f.value)
}

function syncSlider() {
  const idx = activeIndex()
  const el = pillEls[idx]
  if (idx < 0 || !el || !subNavRef.value) return
  const style = {
    left: `${el.offsetLeft}px`,
    top: `${el.offsetTop}px`,
    width: `${el.offsetWidth}px`,
    height: `${el.offsetHeight}px`,
    opacity: '1',
  }
  if (!sliderInit) {
    sliderInit = true
    style.transition = 'none'
    sliderStyle.value = style
    requestAnimationFrame(() => {
      sliderStyle.value = { ...sliderStyle.value, transition: '' }
    })
  } else {
    sliderStyle.value = style
  }
}

watch(() => route.path, () => nextTick(syncSlider))
</script>
