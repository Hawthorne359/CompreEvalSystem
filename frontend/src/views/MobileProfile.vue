<template>
  <div>
  <!-- ═══════════════ 桌面端 ═══════════════ -->
  <div class="hidden md:block">
    <div class="mx-auto max-w-5xl">
      <!-- 页面标题 -->
      <div class="mb-5 flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-slate-800">个人中心</h2>
          <p class="mt-0.5 text-sm text-slate-500">管理您的账号信息与安全设置</p>
        </div>
        <button
          type="button"
          class="rounded-lg border border-slate-200 p-1.5 text-slate-400 hover:text-slate-600"
          title="刷新"
          @click="refreshAll"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
        </button>
      </div>

      <div class="grid grid-cols-3 gap-5">
        <!-- 左栏：用户信息卡 -->
        <div class="col-span-1 space-y-5">
          <div class="app-surface-strong overflow-hidden">
            <div class="flex flex-col items-center px-6 py-8">
              <div
                class="flex h-20 w-20 items-center justify-center rounded-full text-2xl font-bold shadow-lg"
                :class="[avatarColors.bg, avatarColors.text]"
              >
                {{ avatarInitial }}
              </div>
              <h3 class="mt-4 text-lg font-semibold text-slate-800">{{ displayName }}</h3>
              <span class="mt-1 rounded-full bg-slate-100 px-3 py-0.5 text-xs text-slate-600">
                {{ user?.current_role?.name || '未选择角色' }}
              </span>
              <p class="mt-2 text-sm text-slate-400">{{ user?.username }}</p>
              <p v-if="user?.date_joined" class="mt-1 text-xs text-slate-400">
                注册于 {{ formatDate(user.date_joined) }}
              </p>
            </div>
          </div>

          <button
            type="button"
            class="w-full rounded-xl border border-red-200 bg-white px-4 py-2.5 text-sm font-medium text-red-500 transition-colors hover:bg-red-50"
            @click="logout"
          >
            退出登录
          </button>
        </div>

        <!-- 右栏 -->
        <div class="col-span-2 space-y-5">
          <!-- 基本信息 -->
          <div class="app-surface-strong">
            <div class="border-b border-slate-200/80 px-6 py-4">
              <h4 class="text-base font-semibold text-slate-800">基本信息</h4>
              <p class="mt-0.5 text-sm text-slate-500">查看和编辑您的个人信息</p>
            </div>
            <div class="px-6 py-5">
              <div class="grid grid-cols-2 gap-x-8 gap-y-4">
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-500">用户名</label>
                  <p class="text-sm text-slate-800">{{ user?.username || '-' }}</p>
                </div>
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-500">姓名</label>
                  <p class="text-sm text-slate-800">{{ displayName || '-' }}</p>
                </div>
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-500">性别</label>
                  <p class="text-sm text-slate-800">{{ genderLabel }}</p>
                </div>
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-500">院系</label>
                  <p class="text-sm text-slate-800">{{ user?.department_name || '-' }}</p>
                </div>
                <div>
                  <label class="mb-1 block text-xs font-medium text-slate-500">班级</label>
                  <p class="text-sm text-slate-800">{{ user?.class_name || '-' }}</p>
                </div>
              </div>

              <!-- 可编辑字段 -->
              <div class="mt-6 border-t border-slate-100 pt-5">
                <form class="flex flex-col gap-4" @submit.prevent="submitProfile">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="mb-1 block text-sm font-medium text-slate-700">邮箱</label>
                      <input
                        v-model="profileForm.email"
                        type="email"
                        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20"
                        placeholder="your@email.com"
                      />
                    </div>
                    <div>
                      <label class="mb-1 block text-sm font-medium text-slate-700">手机号</label>
                      <input
                        v-model="profileForm.phone"
                        type="tel"
                        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20"
                        placeholder="请输入手机号"
                      />
                    </div>
                  </div>
                  <p v-if="profileError" class="text-sm text-red-600">{{ profileError }}</p>
                  <p v-if="profileSuccess" class="text-sm text-green-600">{{ profileSuccess }}</p>
                  <div class="flex justify-end">
                    <button
                      type="submit"
                      class="rounded-lg bg-brand-500 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-600 disabled:opacity-50"
                      :disabled="profileSaving"
                    >
                      {{ profileSaving ? '保存中…' : '保存修改' }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <!-- 强制改密提示 -->
          <div
            v-if="forceChangePassword"
            class="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-800"
          >
            <p class="font-semibold">您的密码为系统初始密码，请立即修改以保障账号安全。</p>
            <p class="mt-1 text-xs text-red-600">修改密码前无法访问系统其他功能。</p>
          </div>

          <!-- 安全设置 -->
          <div class="app-surface-strong">
            <div class="border-b border-slate-200/80 px-6 py-4">
              <h4 class="text-base font-semibold text-slate-800">安全设置</h4>
              <p class="mt-0.5 text-sm text-slate-500">定期修改密码有助于保障账号安全</p>
            </div>
            <form class="space-y-4 px-6 py-5" @submit.prevent="submitChangePassword">
              <div>
                <label class="mb-1 block text-sm font-medium text-slate-700">当前密码</label>
                <input
                  v-model="changePwForm.oldPassword"
                  type="password"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20"
                  placeholder="请输入当前密码"
                  autocomplete="current-password"
                />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">新密码</label>
                  <input
                    v-model="changePwForm.newPassword"
                    type="password"
                    class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20"
                    placeholder="至少 6 位"
                    autocomplete="new-password"
                  />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-slate-700">确认新密码</label>
                  <input
                    v-model="changePwForm.confirmPassword"
                    type="password"
                    class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 transition-colors focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20"
                    placeholder="再次输入新密码"
                    autocomplete="new-password"
                  />
                </div>
              </div>
              <p v-if="changePwError" class="text-sm text-red-600">{{ changePwError }}</p>
              <p v-if="changePwSuccess" class="text-sm text-green-600">{{ changePwSuccess }}</p>
              <div class="flex justify-end">
                <button
                  type="submit"
                  class="rounded-lg bg-brand-500 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-600 disabled:opacity-50"
                  :disabled="changePwLoading"
                >
                  {{ changePwLoading ? '提交中…' : '确认修改' }}
                </button>
              </div>
            </form>
          </div>

          <!-- 最近登录记录 -->
          <div class="app-surface-strong">
            <div class="border-b border-slate-200/80 px-6 py-4">
              <h4 class="text-base font-semibold text-slate-800">最近登录记录</h4>
              <p class="mt-0.5 text-sm text-slate-500">最近 10 次登录的时间、IP 和设备信息</p>
            </div>
            <div v-if="loginHistoryLoading" class="flex items-center justify-center py-8">
              <div class="h-5 w-5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
              <span class="ml-2 text-sm text-slate-500">加载中…</span>
            </div>
            <div v-else-if="loginHistory.length === 0" class="px-6 py-8 text-center text-sm text-slate-400">
              暂无登录记录
            </div>
            <div v-else class="divide-y divide-slate-100">
              <div
                v-for="(log, idx) in loginHistory"
                :key="log.id"
                class="flex items-center gap-4 px-6 py-3.5"
                :class="idx === 0 ? 'bg-brand-50/40' : ''"
              >
                <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full" :class="idx === 0 ? 'bg-brand-100 text-brand-600' : 'bg-slate-100 text-slate-500'">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <template v-if="isMobileUA(log.user_agent)">
                      <rect x="7" y="2" width="10" height="20" rx="2" /><line x1="12" y1="18" x2="12" y2="18.01" />
                    </template>
                    <template v-else>
                      <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
                    </template>
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-slate-800">{{ parseUA(log.user_agent).browser }}</span>
                    <span v-if="idx === 0" class="rounded bg-brand-500 px-1.5 py-0.5 text-[10px] font-medium text-white">当前</span>
                  </div>
                  <p class="mt-0.5 text-xs text-slate-500">
                    {{ parseUA(log.user_agent).os }}
                    <span v-if="log.ip_address" class="ml-2">IP: {{ log.ip_address }}</span>
                  </p>
                </div>
                <span class="flex-shrink-0 text-xs text-slate-400">{{ formatDateTime(log.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 桌面端：角色切换密码弹窗 -->
    <Teleport to="body">
      <Transition name="page-fade">
        <div
          v-if="showPasswordModal"
          class="fixed inset-0 z-[100] hidden md:flex items-center justify-center bg-black/40 p-4"
          @click.self="cancelPasswordModal"
        >
          <div class="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 shadow-2xl">
            <h3 class="text-base font-medium text-slate-800">切换到「{{ pendingRole?.name }}」角色</h3>
            <p class="mt-1 text-sm text-slate-500">目标角色权限较高，请输入登录密码以验证身份</p>
            <input
              ref="passwordInputDesktop"
              v-model="switchPassword"
              type="password"
              class="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/20"
              placeholder="请输入密码"
              @keydown.enter="confirmSwitchRole"
            />
            <p v-if="passwordModalError" class="mt-2 text-sm text-red-600">{{ passwordModalError }}</p>
            <div class="mt-4 flex justify-end gap-2">
              <button
                type="button"
                class="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                @click="cancelPasswordModal"
              >
                取消
              </button>
              <button
                type="button"
                class="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"
                :disabled="switchRoleLoading"
                @click="confirmSwitchRole"
              >
                {{ switchRoleLoading ? '验证中…' : '确认' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>

  <!-- ═══════════════ 移动端 ═══════════════ -->
  <div class="page-shell pb-6 md:hidden">
    <!-- 用户信息卡 -->
    <div class="glass-card p-5">
      <div class="flex items-center gap-4">
        <div
          class="flex h-14 w-14 items-center justify-center rounded-full text-xl font-bold"
          :class="[avatarColors.bg, avatarColors.text]"
        >
          {{ avatarInitial }}
        </div>
        <div class="flex-1 min-w-0">
          <h2 class="text-lg font-semibold text-slate-800 truncate">{{ displayName }}</h2>
          <p class="mt-0.5 text-sm text-slate-500">{{ user?.current_role?.name || '未选择角色' }}</p>
          <p class="mt-0.5 text-xs text-slate-400">{{ user?.username }}</p>
        </div>
      </div>
    </div>

    <!-- 角色切换（移动端保留，因为移动端底部 Tab 无法切换角色） -->
    <div v-if="hasMultipleRoles" class="glass-card p-4">
      <h3 class="mb-3 text-sm font-medium text-slate-700">切换角色</h3>
      <div class="role-switch-grid" :class="roleGridClass">
        <button
          v-for="(r, idx) in roleList"
          :key="r.id"
          type="button"
          class="role-switch-btn"
          :class="[
            user?.current_role?.id === r.id
              ? 'role-switch-btn--active'
              : 'role-switch-btn--idle',
            roleItemSpanClass(idx),
          ]"
          @click="onSelectRole(r)"
        >
          {{ r.name }}
        </button>
      </div>
    </div>

    <!-- 个人信息 -->
    <div class="glass-card p-4">
      <h3 class="mb-3 text-sm font-medium text-slate-700">个人信息</h3>
      <div class="space-y-2.5">
        <div class="flex items-center justify-between text-sm">
          <span class="text-slate-500">院系</span>
          <span class="text-slate-800">{{ user?.department_name || '-' }}</span>
        </div>
        <div class="flex items-center justify-between text-sm">
          <span class="text-slate-500">班级</span>
          <span class="text-slate-800">{{ user?.class_name || '-' }}</span>
        </div>
        <div class="flex items-center justify-between text-sm">
          <span class="text-slate-500">邮箱</span>
          <span class="text-slate-800">{{ user?.email || '-' }}</span>
        </div>
        <div class="flex items-center justify-between text-sm">
          <span class="text-slate-500">手机号</span>
          <span class="text-slate-800">{{ user?.phone || '-' }}</span>
        </div>
      </div>
      <button
        type="button"
        class="mt-4 w-full rounded-xl border border-brand-200 bg-brand-50/50 py-2.5 text-sm font-medium text-brand-600 active:scale-[0.98] transition-transform"
        @click="showEditProfileModal = true"
      >
        编辑联系方式
      </button>
    </div>

    <!-- 功能入口 -->
    <div class="glass-card p-4">
      <h3 class="mb-3 text-sm font-medium text-slate-700">功能</h3>
      <div class="grid grid-cols-3 gap-3">
        <button type="button" class="profile-grid-item" @click="showChangePwModal = true">
          <svg class="h-6 w-6 text-rose-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></svg>
          <span class="text-xs text-slate-600">修改密码</span>
        </button>
        <button type="button" class="profile-grid-item" @click="showLoginHistoryModal = true; loadLoginHistory()">
          <svg class="h-6 w-6 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v4l3 3" /><circle cx="12" cy="12" r="9" /></svg>
          <span class="text-xs text-slate-600">登录记录</span>
        </button>
        <router-link v-if="level < ROLE_LEVEL_SUPERADMIN" :to="{ name: 'MyOperationLog' }" class="profile-grid-item">
          <svg class="h-6 w-6 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14,2 14,8 20,8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
          <span class="text-xs text-slate-600">操作记录</span>
        </router-link>
      </div>
    </div>

    <button
      type="button"
      class="glass-card w-full py-3.5 text-center text-sm font-medium text-red-500 active:scale-[0.98] transition-transform"
      @click="logout"
    >
      退出登录
    </button>

    <!-- 移动端：角色切换密码弹窗 -->
    <Teleport to="body">
      <Transition name="page-fade">
        <div
          v-if="showPasswordModal"
          class="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 md:hidden"
          @click.self="cancelPasswordModal"
        >
          <div class="w-full max-w-md rounded-t-2xl bg-white p-5 shadow-2xl">
            <h3 class="text-base font-medium text-slate-800">切换到「{{ pendingRole?.name }}」角色</h3>
            <p class="mt-1 text-sm text-slate-500">目标角色权限较高，请输入登录密码以验证身份</p>
            <input
              ref="passwordInputMobile"
              v-model="switchPassword"
              type="password"
              class="app-input mt-3"
              placeholder="请输入密码"
              @keydown.enter="confirmSwitchRole"
            />
            <p v-if="passwordModalError" class="mt-2 text-sm text-red-600">{{ passwordModalError }}</p>
            <div class="mt-4 flex gap-2">
              <button
                type="button"
                class="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm text-slate-600 active:scale-95 transition-transform"
                @click="cancelPasswordModal"
              >
                取消
              </button>
              <button
                type="button"
                class="flex-1 rounded-xl bg-brand-500 py-2.5 text-sm font-medium text-white active:scale-95 transition-transform"
                :disabled="switchRoleLoading"
                @click="confirmSwitchRole"
              >
                {{ switchRoleLoading ? '验证中…' : '确认' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 移动端：修改密码弹窗 -->
    <Teleport to="body">
      <Transition name="page-fade">
        <div
          v-if="showChangePwModal"
          class="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 md:hidden"
          @click.self="showChangePwModal = false"
        >
          <div class="w-full max-w-md rounded-t-2xl bg-white p-5 shadow-2xl">
            <h3 class="text-base font-medium text-slate-800">修改密码</h3>
            <p class="mt-1 text-sm text-slate-500">请输入旧密码和新密码</p>
            <p v-if="forceChangePassword" class="mt-2 rounded bg-red-50 px-3 py-2 text-xs text-red-700 font-medium">
              您的密码为系统初始密码，必须修改后才能继续使用系统。
            </p>
            <form class="mt-3 space-y-3" @submit.prevent="submitChangePassword">
              <input v-model="changePwForm.oldPassword" type="password" class="app-input" placeholder="当前密码" autocomplete="current-password" />
              <input v-model="changePwForm.newPassword" type="password" class="app-input" placeholder="新密码（至少6位）" autocomplete="new-password" />
              <input v-model="changePwForm.confirmPassword" type="password" class="app-input" placeholder="确认新密码" autocomplete="new-password" />
              <p v-if="changePwError" class="text-sm text-red-600">{{ changePwError }}</p>
              <p v-if="changePwSuccess" class="text-sm text-green-600">{{ changePwSuccess }}</p>
              <div class="flex gap-2">
                <button type="button" class="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm text-slate-600 active:scale-95 transition-transform" @click="closeChangePwModal">取消</button>
                <button type="submit" class="flex-1 rounded-xl bg-brand-500 py-2.5 text-sm font-medium text-white active:scale-95 transition-transform" :disabled="changePwLoading">{{ changePwLoading ? '提交中…' : '确认修改' }}</button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 移动端：编辑联系方式弹窗 -->
    <Teleport to="body">
      <Transition name="page-fade">
        <div
          v-if="showEditProfileModal"
          class="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 md:hidden"
          @click.self="showEditProfileModal = false"
        >
          <div class="w-full max-w-md rounded-t-2xl bg-white p-5 shadow-2xl">
            <h3 class="text-base font-medium text-slate-800">编辑联系方式</h3>
            <p class="mt-1 text-sm text-slate-500">修改邮箱或手机号</p>
            <form class="mt-3 space-y-3" @submit.prevent="submitProfile">
              <div>
                <label class="mb-1 block text-sm text-slate-600">邮箱</label>
                <input v-model="profileForm.email" type="email" class="app-input" placeholder="your@email.com" />
              </div>
              <div>
                <label class="mb-1 block text-sm text-slate-600">手机号</label>
                <input v-model="profileForm.phone" type="tel" class="app-input" placeholder="请输入手机号" />
              </div>
              <p v-if="profileError" class="text-sm text-red-600">{{ profileError }}</p>
              <p v-if="profileSuccess" class="text-sm text-green-600">{{ profileSuccess }}</p>
              <div class="flex gap-2">
                <button type="button" class="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm text-slate-600 active:scale-95 transition-transform" @click="showEditProfileModal = false">取消</button>
                <button type="submit" class="flex-1 rounded-xl bg-brand-500 py-2.5 text-sm font-medium text-white active:scale-95 transition-transform" :disabled="profileSaving">{{ profileSaving ? '保存中…' : '保存' }}</button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 移动端：登录记录弹窗 -->
    <Teleport to="body">
      <Transition name="page-fade">
        <div
          v-if="showLoginHistoryModal"
          class="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 md:hidden"
          @click.self="showLoginHistoryModal = false"
        >
          <div class="w-full max-w-md rounded-t-2xl bg-white shadow-2xl" style="max-height: 70vh;">
            <div class="sticky top-0 flex items-center justify-between border-b border-slate-100 bg-white px-5 py-4 rounded-t-2xl">
              <h3 class="text-base font-medium text-slate-800">最近登录记录</h3>
              <button type="button" class="text-slate-400 hover:text-slate-600" @click="showLoginHistoryModal = false">
                <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>
            <div class="overflow-y-auto px-5 pb-5" style="max-height: calc(70vh - 60px);">
              <div v-if="loginHistoryLoading" class="flex items-center justify-center py-8">
                <div class="h-5 w-5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
                <span class="ml-2 text-sm text-slate-500">加载中…</span>
              </div>
              <div v-else-if="loginHistory.length === 0" class="py-8 text-center text-sm text-slate-400">暂无登录记录</div>
              <div v-else class="divide-y divide-slate-100">
                <div v-for="(log, idx) in loginHistory" :key="log.id" class="py-3">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-slate-800">{{ parseUA(log.user_agent).browser }}</span>
                    <span v-if="idx === 0" class="rounded bg-brand-500 px-1.5 py-0.5 text-[10px] font-medium text-white">当前</span>
                  </div>
                  <p class="mt-0.5 text-xs text-slate-500">
                    {{ parseUA(log.user_agent).os }}
                    <span v-if="log.ip_address" class="ml-2">IP: {{ log.ip_address }}</span>
                  </p>
                  <p class="mt-0.5 text-xs text-slate-400">{{ formatDateTime(log.created_at) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
  </div>
</template>

<script setup>
/**
 * @file 个人中心页面。
 * 桌面端：标准 app-surface 卡片布局，包含基本信息、联系方式编辑、安全设置、登录历史。
 * 移动端：glass-card 风格，功能入口 + 弹窗式编辑。
 * 不含角色切换（桌面端顶栏已有）、不含快捷导航入口（导航栏已有）。
 */
import { computed, ref, reactive, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ROLE_LEVEL_SUPERADMIN } from '@/constants/roles'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { changePassword, getLoginHistory, updateProfile } from '@/api/admin'
import { getAvatarInitial, getAvatarColor } from '@/composables/useAvatar'
import { formatDateTime, formatDate } from '@/utils/format'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const user = computed(() => auth.user)
const level = computed(() => user.value?.current_role?.level ?? -1)

/** 是否处于强制改密模式（路由 query 或 user.must_change_password） */
const forceChangePassword = computed(() =>
  route.query.force_change_password === '1' || user.value?.must_change_password,
)

const displayName = computed(() => {
  const u = user.value
  if (!u) return ''
  return u.name || u.username || ''
})

const avatarInitial = computed(() => getAvatarInitial(displayName.value))
const avatarColors = computed(() => getAvatarColor(user.value?.username))

const genderLabel = computed(() => {
  const g = user.value?.gender
  if (g === 'M') return '男'
  if (g === 'F') return '女'
  return '未设置'
})

/** @description 去重后的角色列表，按 level 降序排列（高权限在前） */
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

const hasMultipleRoles = computed(() => roleList.value.length > 1)

/**
 * 根据角色数量决定网格布局 class：
 * 1~4个：单行等宽（grid-cols-N）
 * 5个：6列网格，上2下3（前2个 span-3，后3个 span-2）
 * @returns {string}
 */
const roleGridClass = computed(() => {
  const n = roleList.value.length
  if (n <= 1) return 'grid-cols-1'
  if (n === 2) return 'grid-cols-2'
  if (n === 3) return 'grid-cols-3'
  if (n === 4) return 'grid-cols-4'
  return 'grid-cols-6'
})

/**
 * 5 个角色时前 2 个各占 3 列，后 3 个各占 2 列，其余情况不加额外 span
 * @param {number} idx
 * @returns {string}
 */
function roleItemSpanClass(idx) {
  if (roleList.value.length === 5) {
    return idx < 2 ? 'col-span-3' : 'col-span-2'
  }
  return ''
}

/* ── 角色切换（移动端用） ── */
const showPasswordModal = ref(false)
const switchPassword = ref('')
const passwordModalError = ref('')
const switchRoleLoading = ref(false)
const pendingRole = ref(null)
const passwordInputDesktop = ref(null)
const passwordInputMobile = ref(null)

/**
 * @param {Object} role - { id, code, name, level }
 */
function onSelectRole(role) {
  if (role.id === user.value?.current_role?.id) return
  const currentLevel = user.value?.current_role?.level ?? -1
  const targetLevel = role?.level ?? -1
  if (targetLevel > currentLevel) {
    pendingRole.value = role
    switchPassword.value = ''
    passwordModalError.value = ''
    showPasswordModal.value = true
    nextTick(() => {
      passwordInputDesktop.value?.focus()
      passwordInputMobile.value?.focus()
    })
  } else {
    doSwitchRole(role.id, '')
  }
}

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
 * @param {number} roleId
 * @param {string} password
 */
async function doSwitchRole(roleId, password) {
  await auth.switchRole(roleId, password)
  router.push({ name: 'Dashboard' })
}

function cancelPasswordModal() {
  showPasswordModal.value = false
  pendingRole.value = null
  switchPassword.value = ''
  passwordModalError.value = ''
}

/* ── 修改密码 ── */
const changePwLoading = ref(false)
const changePwError = ref('')
const changePwSuccess = ref('')
const changePwForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const showChangePwModal = ref(false)

function closeChangePwModal() {
  if (forceChangePassword.value) return
  showChangePwModal.value = false
  changePwForm.oldPassword = ''
  changePwForm.newPassword = ''
  changePwForm.confirmPassword = ''
  changePwError.value = ''
  changePwSuccess.value = ''
}

async function submitChangePassword() {
  changePwError.value = ''
  changePwSuccess.value = ''
  if (!changePwForm.oldPassword) { changePwError.value = '请输入当前密码'; return }
  if (changePwForm.newPassword.length < 6) { changePwError.value = '新密码长度不能少于 6 位'; return }
  if (changePwForm.newPassword !== changePwForm.confirmPassword) { changePwError.value = '两次输入的新密码不一致'; return }
  changePwLoading.value = true
  try {
    await changePassword(changePwForm.oldPassword, changePwForm.newPassword)
    changePwSuccess.value = '密码修改成功，下次登录请使用新密码'
    changePwForm.oldPassword = ''
    changePwForm.newPassword = ''
    changePwForm.confirmPassword = ''
    if (forceChangePassword.value) {
      auth.user.must_change_password = false
      setTimeout(() => router.replace({ name: 'Dashboard' }), 1200)
    }
  } catch (e) {
    changePwError.value = e.response?.data?.detail ?? '密码修改失败'
  } finally {
    changePwLoading.value = false
  }
}

/* ── 个人信息编辑 ── */
const profileForm = reactive({ email: '', phone: '' })
const profileSaving = ref(false)
const profileError = ref('')
const profileSuccess = ref('')
const showEditProfileModal = ref(false)

function initProfileForm() {
  profileForm.email = user.value?.email || ''
  profileForm.phone = user.value?.phone || ''
}

async function submitProfile() {
  profileError.value = ''
  profileSuccess.value = ''
  profileSaving.value = true
  try {
    await updateProfile({ email: profileForm.email, phone: profileForm.phone })
    await auth.fetchMe()
    profileSuccess.value = '信息已更新'
    showEditProfileModal.value = false
  } catch (e) {
    profileError.value = e.response?.data?.detail ?? '保存失败'
  } finally {
    profileSaving.value = false
  }
}

/* ── 登录历史 ── */
const loginHistory = ref([])
const loginHistoryLoading = ref(false)
const showLoginHistoryModal = ref(false)

async function loadLoginHistory() {
  loginHistoryLoading.value = true
  try {
    loginHistory.value = await getLoginHistory()
  } catch {
    loginHistory.value = []
  } finally {
    loginHistoryLoading.value = false
  }
}

/* ── 工具函数 ── */

/**
 * 解析 User-Agent 字符串为浏览器和操作系统的友好名称
 * @param {string} ua
 * @returns {{ browser: string, os: string }}
 */
function parseUA(ua) {
  if (!ua) return { browser: '未知浏览器', os: '未知设备' }
  let browser = '浏览器'
  if (ua.includes('Edg/') || ua.includes('Edge/')) browser = 'Edge'
  else if (ua.includes('Chrome/') && !ua.includes('Edg')) browser = 'Chrome'
  else if (ua.includes('Firefox/')) browser = 'Firefox'
  else if (ua.includes('Safari/') && !ua.includes('Chrome')) browser = 'Safari'

  let os = '其他'
  if (ua.includes('Windows NT 10')) os = 'Windows 10/11'
  else if (ua.includes('Windows')) os = 'Windows'
  else if (ua.includes('Mac OS X')) os = 'macOS'
  else if (ua.includes('iPhone')) os = 'iPhone'
  else if (ua.includes('iPad')) os = 'iPad'
  else if (ua.includes('Android')) os = 'Android'
  else if (ua.includes('Linux')) os = 'Linux'

  return { browser, os }
}

/** @param {string} ua */
function isMobileUA(ua) {
  if (!ua) return false
  return /iPhone|iPad|Android|Mobile/i.test(ua)
}

function refreshAll() {
  auth.fetchMe()
  loadLoginHistory()
  initProfileForm()
}

function logout() {
  auth.logout()
  router.push({ name: 'Login' })
}

onMounted(() => {
  initProfileForm()
  loadLoginHistory()
  if (forceChangePassword.value) {
    showChangePwModal.value = true
  }
})

useRealtimeRefresh('user', refreshAll)
</script>

<style scoped>
.role-switch-grid {
  display: grid;
  gap: 8px;
}

.role-switch-btn {
  @apply rounded-xl py-2.5 text-sm font-medium transition-all text-center;
}

.role-switch-btn--active {
  @apply bg-brand-500 text-white shadow-md;
  box-shadow: 0 4px 12px rgba(200, 16, 46, 0.25);
}

.role-switch-btn--idle {
  @apply bg-white/60 text-slate-600 border border-slate-200/60;
  -webkit-tap-highlight-color: transparent;
}

.role-switch-btn--idle:active {
  transform: scale(0.95);
}
</style>
