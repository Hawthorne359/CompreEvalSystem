<template>
  <section class="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h4 class="text-sm font-semibold text-slate-800">映射配置</h4>
      <div class="flex items-center gap-2">
        <button type="button" class="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-50" @click="$emit('new')">
          新建映射
        </button>
        <button type="button" class="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-50" @click="$emit('saveAs')">
          另存为
        </button>
      </div>
    </div>

    <div class="mt-3 grid gap-2 sm:grid-cols-2">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">当前映射</label>
        <select
          :value="selectedMappingId ?? ''"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
          @change="$emit('select', $event.target.value)"
        >
          <option value="">请选择映射</option>
          <option v-for="item in mappingList" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">映射名称</label>
        <input
          :value="draft.name"
          type="text"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
          placeholder="例如：2024级班级总表"
          @input="$emit('update:name', $event.target.value)"
        />
      </div>
    </div>

    <label class="mt-3 inline-flex items-center gap-2 text-sm text-slate-700">
      <input
        :checked="!!draft.is_default"
        type="checkbox"
        class="cursor-pointer"
        @change="$emit('update:isDefault', $event.target.checked)"
      />
      设为该导出类型默认映射
    </label>
  </section>
</template>

<script setup>
defineProps({
  mappingList: { type: Array, default: () => [] },
  selectedMappingId: { type: [Number, String, null], default: null },
  draft: { type: Object, required: true },
})

defineEmits(['new', 'saveAs', 'select', 'update:name', 'update:isDefault'])
</script>
