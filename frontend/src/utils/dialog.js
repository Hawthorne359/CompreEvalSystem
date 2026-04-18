import { reactive } from 'vue'

const defaultState = {
  visible: false,
  mode: 'alert',
  title: '',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  danger: false,
  inputType: 'text',
  inputPlaceholder: '',
  inputValue: '',
  inputLabel: '',
  inputRequired: false,
  inputValidator: null,
}

export const dialogState = reactive({
  ...defaultState,
  error: '',
  _resolver: null,
})

function resetDialogState() {
  Object.assign(dialogState, {
    ...defaultState,
    error: '',
    _resolver: null,
  })
}

function openDialog(options = {}) {
  return new Promise((resolve) => {
    Object.assign(dialogState, {
      ...defaultState,
      ...options,
      visible: true,
      error: '',
      _resolver: resolve,
    })
  })
}

export function openAlert(options = {}) {
  return openDialog({
    mode: 'alert',
    title: options.title || '提示',
    message: options.message || '',
    confirmText: options.confirmText || '我知道了',
    danger: !!options.danger,
  })
}

export function openConfirm(options = {}) {
  return openDialog({
    mode: 'confirm',
    title: options.title || '操作确认',
    message: options.message || '',
    confirmText: options.confirmText || '确认',
    cancelText: options.cancelText || '取消',
    danger: !!options.danger,
  })
}

export function openPrompt(options = {}) {
  return openDialog({
    mode: 'prompt',
    title: options.title || '请输入',
    message: options.message || '',
    confirmText: options.confirmText || '确认',
    cancelText: options.cancelText || '取消',
    inputType: options.inputType || 'text',
    inputLabel: options.inputLabel || '',
    inputPlaceholder: options.inputPlaceholder || '',
    inputValue: options.defaultValue ?? '',
    inputRequired: !!options.inputRequired,
    inputValidator: typeof options.inputValidator === 'function' ? options.inputValidator : null,
    danger: !!options.danger,
  })
}

export function closeDialog(payload) {
  const resolver = dialogState._resolver
  resetDialogState()
  if (resolver) resolver(payload)
}

