/**
 * @file 登录凭据本地加密存储工具。
 * 使用 Base64 混淆 + 简单异或加密存储用户名和密码，防止明文泄露。
 * 注意：前端加密无法替代 HTTPS，仅作为防止浏览器本地存储明文的辅助手段。
 */

const STORAGE_KEY_USERNAME = '__ce_ru'
const STORAGE_KEY_PASSWORD = '__ce_rp'
const STORAGE_KEY_REMEMBER_USER = '__ce_rem_u'
const STORAGE_KEY_REMEMBER_PASS = '__ce_rem_p'
const CIPHER_KEY = 'CES@2026#sut'

/**
 * 简单异或加密/解密（对称）。
 * @param {string} text
 * @param {string} key
 * @returns {string}
 */
function xorCipher(text, key) {
  let result = ''
  for (let i = 0; i < text.length; i++) {
    result += String.fromCharCode(text.charCodeAt(i) ^ key.charCodeAt(i % key.length))
  }
  return result
}

/**
 * @param {string} text
 * @returns {string}
 */
function encode(text) {
  return btoa(unescape(encodeURIComponent(xorCipher(text, CIPHER_KEY))))
}

/**
 * @param {string} encoded
 * @returns {string}
 */
function decode(encoded) {
  try {
    return xorCipher(decodeURIComponent(escape(atob(encoded))), CIPHER_KEY)
  } catch {
    return ''
  }
}

/**
 * 保存凭据到 localStorage。
 * @param {{ username: string, password: string, rememberUser: boolean, rememberPass: boolean }} opts
 */
export function saveCredentials({ username, password, rememberUser, rememberPass }) {
  localStorage.setItem(STORAGE_KEY_REMEMBER_USER, rememberUser ? '1' : '0')
  localStorage.setItem(STORAGE_KEY_REMEMBER_PASS, rememberPass ? '1' : '0')

  if (rememberUser) {
    localStorage.setItem(STORAGE_KEY_USERNAME, encode(username))
  } else {
    localStorage.removeItem(STORAGE_KEY_USERNAME)
  }

  if (rememberPass) {
    localStorage.setItem(STORAGE_KEY_PASSWORD, encode(password))
  } else {
    localStorage.removeItem(STORAGE_KEY_PASSWORD)
  }
}

/**
 * 从 localStorage 读取已保存的凭据。
 * @returns {{ username: string, password: string, rememberUser: boolean, rememberPass: boolean }}
 */
export function loadCredentials() {
  const rememberUser = localStorage.getItem(STORAGE_KEY_REMEMBER_USER) === '1'
  const rememberPass = localStorage.getItem(STORAGE_KEY_REMEMBER_PASS) === '1'

  let username = ''
  let password = ''

  if (rememberUser) {
    const raw = localStorage.getItem(STORAGE_KEY_USERNAME)
    if (raw) username = decode(raw)
  }

  if (rememberPass) {
    const raw = localStorage.getItem(STORAGE_KEY_PASSWORD)
    if (raw) password = decode(raw)
  }

  return { username, password, rememberUser, rememberPass }
}
