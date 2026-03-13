<template>
  <div class="login-page" @mousemove="onMouseMove">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>

    <div class="card">
      <!-- 左区 / 移动端上区：深色 + 校徽 -->
      <div class="card-brand">
        <div class="brand-bg"></div>
        <div class="brand-content">
          <div
            ref="discRef"
            class="disc"
            :style="{
              transform: `perspective(800px) rotateY(${d.ry}deg) rotateX(${d.rx}deg) rotateZ(${d.rz}deg)`,
              boxShadow: `${d.sx}px 10px 36px rgba(0,0,0,0.22), ${d.sx * .4}px 4px 14px rgba(0,0,0,0.12), inset 0 2px 1px rgba(255,255,255,0.7), inset 0 -2px 6px rgba(0,0,0,0.08)`
            }"
          >
            <div
              class="disc-shine"
              :style="{ background: `linear-gradient(${d.sa}deg, rgba(255,255,255,${d.so}) 0%, rgba(255,255,255,0.1) 40%, transparent 65%)` }"
            ></div>
            <div class="disc-rim"></div>
            <div class="disc-inner">
              <img src="@/assets/logo.svg" alt="校徽" class="logo-img" />
            </div>
          </div>
          <h2 class="brand-title">陕西理工大学</h2>
          <p class="brand-sub">Shaanxi University of Technology</p>
        </div>
      </div>

      <!-- 右区 / 移动端下区：浅色毛玻璃 + 表单 -->
      <div class="card-form">
        <div class="form-inner">
          <h1 class="form-title">综合素质测评系统</h1>
          <p class="form-subtitle">请登录您的账号以继续</p>

          <form class="login-form" @submit.prevent="onSubmit">
            <div class="input-group">
              <label class="input-label">账号</label>
              <div class="input-wrap">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
                <input
                  v-model="username" type="text" placeholder="请输入用户名"
                  autocomplete="username" required
                  @focus="onFieldFocus('user')" @blur="onFieldBlur"
                />
              </div>
            </div>

            <div class="input-group">
              <label class="input-label">密码</label>
              <div class="input-wrap">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                </svg>
                <input
                  v-model="password" :type="showPw ? 'text' : 'password'" placeholder="请输入密码"
                  autocomplete="current-password" required
                  @focus="onFieldFocus('pw')" @blur="onFieldBlur"
                />
                <button type="button" class="pw-toggle" @click="showPw = !showPw">
                  <svg v-if="!showPw" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12c1.292 4.338 5.31 7.5 10.066 7.5.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                </button>
              </div>
            </div>

            <div class="remember-row">
              <label class="remember-label">
                <input v-model="rememberUser" type="checkbox" class="remember-check" />
                <span>记住账号</span>
              </label>
              <label class="remember-label">
                <input v-model="rememberPass" type="checkbox" class="remember-check" />
                <span>记住密码</span>
              </label>
            </div>

            <p v-if="error" class="error-msg">{{ error }}</p>

            <button type="submit" class="submit-btn" :disabled="loading">
              <span v-if="loading" class="spinner"></span>
              {{ loading ? '登录中…' : '登 录' }}
            </button>
          </form>

          <p class="footer-text">学生综合素质测评管理平台</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @file 登录页 - 一体化斜切卡片 + 3D 校徽 + 输入动效
 */
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { sessionBus } from '@/utils/sessionBus'
import { saveCredentials, loadCredentials } from '@/utils/credentialStorage'
import { stopEventStream } from '@/composables/useEventStream'
import gsap from 'gsap'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPw = ref(false)
const discRef = ref(null)
const rememberUser = ref(true)
const rememberPass = ref(false)

/** @description 圆盘当前渲染值 */
const d = reactive({ rx: 0, ry: 0, rz: 0, sa: 135, so: 0.55, sx: 0 })
/** @description 鼠标追踪目标值 */
const tgt = reactive({ rx: 0, ry: 0, rz: 0, sa: 135, so: 0.55, sx: 0 })
/** @description 输入聚焦附加偏移 */
const focusOff = reactive({ rx: 0, rz: 0, so: 0 })

let raf = 0

/**
 * @param {MouseEvent} e
 */
function onMouseMove(e) {
  const nx = (e.clientX - window.innerWidth / 2) / (window.innerWidth / 2)
  const ny = (window.innerHeight / 2 - e.clientY) / (window.innerHeight / 2)
  tgt.ry = nx * 25
  tgt.rx = ny * 14 + focusOff.rx
  tgt.rz = focusOff.rz
  tgt.sa = 135 - nx * 70
  tgt.so = 0.55 + Math.abs(nx) * 0.15 + focusOff.so
  tgt.sx = -nx * 12
}

function tick() {
  gsap.to(d, {
    rx: tgt.rx, ry: tgt.ry, rz: tgt.rz,
    sa: tgt.sa, so: tgt.so, sx: tgt.sx,
    duration: 0.5, ease: 'power2.out', overwrite: 'auto',
  })
  raf = requestAnimationFrame(tick)
}

/**
 * @param {'user'|'pw'} field
 */
function onFieldFocus(field) {
  if (field === 'user') {
    focusOff.rx = 6
    focusOff.rz = 0
    focusOff.so = 0.12
    gsap.to(discRef.value, { scale: 1.03, duration: 0.4, ease: 'back.out(1.7)' })
  } else {
    focusOff.rx = 0
    focusOff.rz = -10
    focusOff.so = 0.18
    gsap.to(discRef.value, { scale: 1.02, duration: 0.4, ease: 'back.out(1.7)' })
  }
}

function onFieldBlur() {
  focusOff.rx = 0
  focusOff.rz = 0
  focusOff.so = 0
  gsap.to(discRef.value, { scale: 1, duration: 0.5, ease: 'power2.out' })
}

/** 勾选「记住密码」时自动勾选「记住账号」；取消「记住账号」时自动取消「记住密码」 */
watch(rememberPass, (val) => { if (val) rememberUser.value = true })
watch(rememberUser, (val) => { if (!val) rememberPass.value = false })

onMounted(() => {
  raf = requestAnimationFrame(tick)
  const saved = loadCredentials()
  rememberUser.value = saved.rememberUser
  rememberPass.value = saved.rememberPass
  if (saved.username) username.value = saved.username
  if (saved.password) password.value = saved.password
})
onUnmounted(() => { cancelAnimationFrame(raf) })

/** @description 登录提交 */
async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    stopEventStream()
    await auth.login(username.value, password.value)
    saveCredentials({
      username: username.value,
      password: password.value,
      rememberUser: rememberUser.value,
      rememberPass: rememberPass.value,
    })
    sessionBus.emit('login-success')
    if (auth.user?.must_change_password) {
      router.replace({ name: 'Profile', query: { force_change_password: '1' } })
    } else {
      const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
      if (redirect && redirect.startsWith('/')) {
        router.replace(redirect)
      } else {
        router.replace({ name: 'Dashboard' })
      }
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '账号或密码错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ===== 页面 ===== */
.login-page {
  position: fixed; inset: 0;
  background: linear-gradient(150deg, #f2eaec, #ece2e6 35%, #e3d8dc 65%, #efe5e9);
  overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Noto Sans SC', system-ui, sans-serif;
}

/* ===== 光斑 ===== */
.blob { position: absolute; border-radius: 50%; filter: blur(100px); opacity: .5; pointer-events: none; }
.blob-1 { width: 580px; height: 580px; background: radial-gradient(circle, rgba(200,16,46,.1), transparent 70%); top: -14%; left: -8%; animation: b1 17s ease-in-out infinite; }
.blob-2 { width: 480px; height: 480px; background: radial-gradient(circle, rgba(180,120,140,.14), transparent 70%); bottom: -10%; right: -5%; animation: b2 21s ease-in-out infinite; }
.blob-3 { width: 400px; height: 400px; background: radial-gradient(circle, rgba(150,40,65,.08), transparent 70%); top: 42%; left: 48%; transform: translate(-50%,-50%); animation: b3 24s ease-in-out infinite; }
@keyframes b1 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(45px,30px) scale(1.07)} 66%{transform:translate(-20px,45px) scale(.94)} }
@keyframes b2 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(-35px,-20px) scale(1.06)} 66%{transform:translate(28px,-35px) scale(.93)} }
@keyframes b3 { 0%,100%{transform:translate(-50%,-50%) scale(1)} 33%{transform:translate(-46%,-54%) scale(1.09)} 66%{transform:translate(-54%,-46%) scale(.92)} }

/* ===== 一体化卡片 ===== */
.card {
  position: relative; z-index: 1;
  display: flex;
  width: min(1080px, 93vw); height: min(620px, 88vh);
  border-radius: 28px; overflow: hidden;
  box-shadow: 0 20px 64px rgba(60,15,30,.1), 0 8px 24px rgba(0,0,0,.05);
  animation: cardUp .75s ease-out both;
}
@keyframes cardUp { from{opacity:0;transform:translateY(22px) scale(.98)} to{opacity:1;transform:translateY(0) scale(1)} }

/* ===== 左区（品牌区）===== */
.card-brand {
  position: relative;
  flex: 0 0 42%; display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}

.brand-bg {
  position: absolute; inset: 0;
  background: linear-gradient(160deg, #4a1a28 0%, #35121e 50%, #280e16 100%);
}

/* 斜切对角遮罩：深色区右边缘斜切 */
.brand-bg::after {
  content: '';
  position: absolute;
  top: -5%; bottom: -5%; right: -60px; width: 120px;
  background: linear-gradient(150deg, #f2eaec, #ece2e6 40%, rgba(255,255,255,.55));
  transform: skewX(-6deg);
  box-shadow: -4px 0 20px rgba(60,15,30,.08);
}

.brand-content {
  position: relative; z-index: 2;
  display: flex; flex-direction: column; align-items: center; gap: 22px;
  padding: 0 30px;
  animation: fadeUp .7s ease-out .12s both;
}

/* ===== 3D 玻璃圆盘 ===== */
.disc {
  position: relative;
  width: 260px; height: 260px;
  border-radius: 50%;
  background: radial-gradient(ellipse at 40% 35%, rgba(255,255,255,.95), rgba(255,255,255,.82));
  border: 2.5px solid rgba(255,255,255,.85);
  display: flex; align-items: center; justify-content: center;
  will-change: transform, box-shadow;
  transform-style: preserve-3d;
}

.disc-shine {
  position: absolute; inset: -1px; border-radius: 50%;
  pointer-events: none; z-index: 4;
}

.disc-rim {
  position: absolute; inset: -4px; border-radius: 50%;
  border: 4px solid rgba(0,0,0,.03);
  box-shadow: inset 0 3px 5px rgba(255,255,255,.55), inset 0 -3px 8px rgba(0,0,0,.07), 0 1px 3px rgba(0,0,0,.05);
  pointer-events: none; z-index: 3;
}

.disc-inner {
  width: 88%; height: 88%;
  border-radius: 50%; overflow: hidden;
  position: relative; z-index: 2;
  display: flex; align-items: center; justify-content: center;
}

.logo-img {
  width: 100%; height: 100%; object-fit: contain;
  filter: drop-shadow(0 1px 4px rgba(200,16,46,.1));
}

.brand-title {
  color: rgba(255,255,255,.95); font-size: 1.3rem; font-weight: 700;
  letter-spacing: .18em; text-shadow: 0 2px 10px rgba(0,0,0,.25);
}

.brand-sub {
  color: rgba(255,255,255,.4); font-size: .76rem; letter-spacing: .05em; margin-top: -10px;
}

/* ===== 右区（表单区）===== */
.card-form {
  flex: 1; position: relative;
  background: rgba(255,255,255,.5);
  backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
  display: flex; align-items: center; justify-content: center;
}

.form-inner {
  width: 100%; max-width: 370px; padding: 44px 40px;
  animation: fadeUp .7s ease-out .22s both;
}

/* ===== 表单元素 ===== */
.form-title { color: #2a1018; font-size: 1.5rem; font-weight: 700; letter-spacing: .04em; text-align: center; }
.form-subtitle { color: #8a7078; font-size: .84rem; text-align: center; margin-top: 6px; margin-bottom: 28px; }

.login-form { display: flex; flex-direction: column; gap: 17px; }
.input-group { display: flex; flex-direction: column; gap: 5px; }
.input-label { color: #6a555c; font-size: .73rem; font-weight: 600; letter-spacing: .1em; }

.input-wrap { position: relative; display: flex; align-items: center; }
.input-icon { position: absolute; left: 14px; width: 17px; height: 17px; color: #b89ca4; pointer-events: none; transition: color .2s; }
.input-wrap:focus-within .input-icon { color: #c8102e; }

.input-wrap input {
  width: 100%;
  background: rgba(255,255,255,.6);
  border: 1px solid rgba(160,120,135,.17);
  border-radius: 12px; padding: 12px 44px 12px 40px;
  color: #2a1018; font-size: .94rem; outline: none;
  transition: all .25s ease;
}
.input-wrap input::placeholder { color: #baa4aa; }
.input-wrap input:focus { border-color: rgba(200,16,46,.35); background: rgba(255,255,255,.78); box-shadow: 0 0 0 3px rgba(200,16,46,.07); }

.pw-toggle { position: absolute; right: 12px; background: none; border: none; cursor: pointer; padding: 4px; display: flex; align-items: center; justify-content: center; }
.pw-toggle svg { width: 17px; height: 17px; color: #b89ca4; transition: color .2s; }
.pw-toggle:hover svg { color: #6a555c; }

.remember-row { display: flex; align-items: center; gap: 18px; margin-top: -4px; }
.remember-label { display: flex; align-items: center; gap: 5px; cursor: pointer; user-select: none; }
.remember-label span { color: #8a7078; font-size: .8rem; }
.remember-check {
  width: 15px; height: 15px; border-radius: 4px;
  border: 1.5px solid rgba(160,120,135,.3);
  accent-color: #c8102e; cursor: pointer;
}

.error-msg { color: #c62828; font-size: .83rem; text-align: center; padding: 8px 14px; background: rgba(211,47,47,.06); border-radius: 8px; border: 1px solid rgba(211,47,47,.1); }

.submit-btn {
  width: 100%; padding: 13px 0; border: none; border-radius: 12px;
  background: linear-gradient(135deg, #c8102e, #a00d24);
  color: #fff; font-size: .98rem; font-weight: 600; letter-spacing: .2em;
  cursor: pointer; transition: all .25s ease;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin-top: 4px; box-shadow: 0 4px 18px rgba(200,16,46,.22);
}
.submit-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 26px rgba(200,16,46,.32); }
.submit-btn:active:not(:disabled) { transform: translateY(0) scale(.98); }
.submit-btn:disabled { opacity: .6; cursor: not-allowed; }

.spinner { width: 17px; height: 17px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }

.footer-text { color: #a08890; font-size: .74rem; text-align: center; margin-top: 24px; letter-spacing: .04em; }

@keyframes fadeUp { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }

/* ===== 自适应：移动端上下布局 ===== */
@media (max-width: 768px) {
  .card {
    flex-direction: column;
    width: 92vw; height: auto; max-height: 96vh;
    border-radius: 22px;
    overflow-y: auto;
  }

  .card-brand {
    flex: none; height: 220px;
  }

  /* 移动端斜切改为底部水平倾斜 */
  .brand-bg::after {
    top: auto; bottom: -40px; left: -5%; right: -5%;
    width: auto; height: 80px;
    transform: skewY(-3deg);
    box-shadow: 0 -3px 16px rgba(60,15,30,.06);
  }

  .disc {
    width: 130px; height: 130px;
  }

  .brand-title { font-size: 1rem; }
  .brand-sub { font-size: .68rem; margin-top: -6px; text-shadow: 0 1px 4px rgba(0,0,0,.45), 0 0 8px rgba(0,0,0,.2); }
  .brand-content { gap: 12px; padding: 0 20px; }

  .form-inner { padding: 28px 24px 32px; }
  .form-title { font-size: 1.25rem; }
  .form-subtitle { margin-bottom: 20px; }
}

/* ===== 中等屏幕微调 ===== */
@media (min-width: 769px) and (max-width: 1024px) {
  .card { width: 96vw; }
  .card-brand { flex: 0 0 38%; }
  .disc { width: 210px; height: 210px; }
  .brand-title { font-size: 1.1rem; }
  .form-inner { padding: 40px 32px; }
}
</style>
