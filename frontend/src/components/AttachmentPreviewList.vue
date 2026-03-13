<template>
  <div class="space-y-2">
    <div
      v-for="item in normalizedItems"
      :key="item.id"
      class="rounded border border-slate-200 bg-white p-2"
    >
      <div class="mb-2 flex items-start justify-between gap-2 text-xs">
        <div class="min-w-0 truncate text-slate-700">
          {{ item.name || `附件 #${item.id}` }}
        </div>
        <div class="shrink-0 space-x-2">
          <a
            v-if="item.file"
            :href="item.file"
            target="_blank"
            rel="noopener"
            class="app-action app-action-primary"
          >
            打开
          </a>
          <a
            v-if="item.file"
            :href="item.file"
            target="_blank"
            rel="noopener"
            class="app-action app-action-default"
          >
            下载
          </a>
          <button
            v-if="showDelete"
            type="button"
            class="app-action app-action-danger"
            @click="$emit('delete', item)"
          >
            删除
          </button>
        </div>
      </div>

      <img
        v-if="item.previewType === 'image'"
        :src="item.file"
        :alt="item.name || '附件图片'"
        class="max-h-60 w-full rounded border border-slate-100 object-contain"
      />
      <iframe
        v-else-if="item.previewType === 'pdf'"
        :src="item.file"
        class="h-60 w-full rounded border border-slate-100"
        title="PDF 预览"
      />
      <div v-else class="rounded border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-500">
        当前文件类型不支持内嵌预览，请使用上方“打开/下载”查看。
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  showDelete: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['delete'])

/**
 * 根据文件扩展名推断预览类型。
 * @param {string} fileUrl
 * @param {string} fileExt
 * @returns {'image'|'pdf'|'other'}
 */
function detectPreviewType(fileUrl, fileExt) {
  const ext = (fileExt || fileUrl || '').toLowerCase()
  if (/\.(jpg|jpeg|png|gif|webp|bmp)(\?|#|$)/.test(ext) || /^(jpg|jpeg|png|gif|webp|bmp)$/.test(ext)) {
    return 'image'
  }
  if (/\.pdf(\?|#|$)/.test(ext) || ext === 'pdf') {
    return 'pdf'
  }
  return 'other'
}

/**
 * 统一附件项结构，便于页面复用。
 */
const normalizedItems = computed(() => {
  return (props.items || []).map((item) => {
    const file = item?.file || ''
    const fileExt = item?.file_ext || ''
    return {
      id: item?.id,
      name: item?.name || '',
      file,
      file_ext: fileExt,
      previewType: detectPreviewType(file, fileExt),
    }
  })
})
</script>
