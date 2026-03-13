/**
 * 路由：登录、布局内各页（工作台、提交、审核、报表、系统管理等）。
 * 权限控制：
 *   - requiresAuth: 必须登录（有 access token）
 *   - requiresLevel: 最低角色等级，守卫从 Pinia auth store 读取
 *
 * 角色等级约定：
 *   LV0=学生  LV1=学生助理  LV2=评审老师（辅导员）  LV3=院系主任  LV5=超级管理员
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: { name: 'Dashboard' },
    children: [
      { path: 'home', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'my-logs', name: 'MyOperationLog', component: () => import('@/views/MyOperationLog.vue') },
      { path: 'my-logs/:id', name: 'MyOperationLogDetail', component: () => import('@/views/MyOperationLogDetail.vue') },
      { path: 'submissions', name: 'Submissions', component: () => import('@/views/Submissions.vue') },
      { path: 'submissions/new', name: 'SubmissionNew', component: () => import('@/views/SubmissionNew.vue') },
      { path: 'submissions/:id', name: 'SubmissionDetail', component: () => import('@/views/SubmissionDetail.vue') },
      // 学生助理（LV1）：待评分任务
      { path: 'assistant-tasks', name: 'AssistantTasks', component: () => import('@/views/AssistantTasks.vue'), meta: { requiresLevel: 1 } },
      // 评审老师（辅导员）及以上（LV2+）：审核任务
      { path: 'review', name: 'Review', component: () => import('@/views/Review.vue'), meta: { requiresLevel: 2 } },
      { path: 'review/import', name: 'ScoreImport', component: () => import('@/views/ScoreImport.vue'), meta: { requiresLevel: 2 } },
      { path: 'review/:id', name: 'ReviewDetail', component: () => import('@/views/ReviewDetail.vue'), meta: { requiresLevel: 1 } },
      { path: 'appeals', name: 'Appeals', component: () => import('@/views/Appeals.vue') },
      { path: 'appeals/:id', name: 'AppealDetail', component: () => import('@/views/AppealDetail.vue') },
      { path: 'report', name: 'Report', component: () => import('@/views/Report.vue') },
      { path: 'report/submissions/:id', name: 'ReportSubmissionDetail', component: () => import('@/views/ReportSubmissionDetail.vue') },
      { path: 'profile', name: 'Profile', component: () => import('@/views/MobileProfile.vue') },
      // 评审老师（辅导员）及以上（LV2+）：快捷用户导入入口（无需进入系统管理区）
      { path: 'users/import', name: 'UserImportQuick', component: () => import('@/views/UserImport.vue'), meta: { requiresLevel: 2 } },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/Admin.vue'),
        meta: { requiresLevel: 5 },
        children: [
          { path: 'organization', name: 'Organization', component: () => import('@/views/Organization.vue') },
          { path: 'users', name: 'Users', component: () => import('@/views/Users.vue') },
          { path: 'users/new', name: 'UserNew', component: () => import('@/views/UserForm.vue') },
          { path: 'users/:id/edit', name: 'UserEdit', component: () => import('@/views/UserForm.vue') },
          { path: 'users/import', name: 'UserImport', component: () => import('@/views/UserImport.vue') },
          { path: 'seasons', name: 'Seasons', component: () => import('@/views/Seasons.vue') },
          { path: 'seasons/:seasonId/projects', name: 'SeasonProjects', component: () => import('@/views/SeasonProjects.vue') },
          { path: 'projects/:projectId', name: 'ProjectConfig', component: () => import('@/views/ProjectConfig.vue') },
          { path: 'system', name: 'SystemAdmin', component: () => import('@/views/SystemAdmin.vue') },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  let hasToken = !!localStorage.getItem('access')
  if (hasToken) {
    hasToken = await auth.ensureSession()
  }

  // 未登录时拦截需要认证的页面
  if (to.meta.requiresAuth && !hasToken) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  // 已登录时拦截登录页
  if (to.meta.guest && hasToken) {
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : ''
    if (redirect && redirect.startsWith('/')) return next(redirect)
    return next({ name: 'Dashboard' })
  }

  // 强制修改密码：导入用户首次登录须改密后才能访问其他页面
  if (hasToken && auth?.user?.must_change_password) {
    const allowedNames = ['Profile', 'Login']
    if (!allowedNames.includes(to.name)) {
      return next({ name: 'Profile', query: { force_change_password: '1' } })
    }
  }

  // 需要特定角色等级的路由：从 Pinia store 读取当前 level
  const requiredLevel = to.meta.requiresLevel ?? to.matched.find((r) => r.meta?.requiresLevel)?.meta?.requiresLevel
  if (requiredLevel !== undefined && hasToken) {
    const currentLevel = auth?.user?.current_role?.level ?? -1
    if (currentLevel < requiredLevel) {
      return next({ name: 'Dashboard' })
    }
  }

  next()
})

export default router
