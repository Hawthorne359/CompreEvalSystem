/**
 * @file 头像工具：根据用户名生成首字母和品牌色圆形头像的配色方案。
 * 通过字符串哈希确定性地映射到预设调色板，保证同一用户每次生成相同颜色。
 */

/** @type {Array<{bg: string, text: string}>} 预设调色板（Tailwind 兼容的 CSS 类名组合） */
const PALETTE = [
  { bg: 'bg-blue-500',    text: 'text-white' },
  { bg: 'bg-emerald-500', text: 'text-white' },
  { bg: 'bg-violet-500',  text: 'text-white' },
  { bg: 'bg-amber-500',   text: 'text-white' },
  { bg: 'bg-rose-500',    text: 'text-white' },
  { bg: 'bg-cyan-500',    text: 'text-white' },
  { bg: 'bg-indigo-500',  text: 'text-white' },
  { bg: 'bg-teal-500',    text: 'text-white' },
  { bg: 'bg-pink-500',    text: 'text-white' },
  { bg: 'bg-orange-500',  text: 'text-white' },
]

/**
 * djb2 字符串哈希，用于将用户名映射到调色板索引
 * @param {string} str
 * @returns {number}
 */
function hashCode(str) {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) >>> 0
  }
  return hash
}

/**
 * 根据用户名/显示名获取头像首字母
 * @param {string} displayName - 显示名（中文姓名或英文用户名）
 * @returns {string} 首字母（大写）
 */
export function getAvatarInitial(displayName) {
  if (!displayName) return '?'
  return displayName.charAt(0).toUpperCase()
}

/**
 * 根据用户名获取确定性的头像背景色 CSS 类
 * @param {string} username - 用户名（用于哈希）
 * @returns {{ bg: string, text: string }} Tailwind 类名
 */
export function getAvatarColor(username) {
  if (!username) return PALETTE[0]
  const idx = hashCode(username) % PALETTE.length
  return PALETTE[idx]
}
