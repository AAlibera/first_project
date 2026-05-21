<script setup lang="ts">
import { ref, computed } from 'vue'
import { Trash2, Eye, Clock, Target } from 'lucide-vue-next'
import type { HistoryItem } from '@/types'

const props = defineProps<{
  item: HistoryItem
}>()

const emit = defineEmits<{
  view: [id: string]
  delete: [id: string]
}>()

const isHovered = ref(false)

const formattedTime = computed(() => {
  const date = new Date(props.item.created_at)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})
</script>

<template>
  <div
    class="card overflow-hidden group relative"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <div class="relative aspect-video overflow-hidden">
      <img
        :src="item.result_image_url"
        :alt="item.filename"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div class="absolute bottom-3 left-3 right-3 flex justify-between items-center">
          <button
            @click="emit('view', item.id)"
            class="flex items-center space-x-2 px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg text-white hover:bg-white/30 transition-all"
          >
            <Eye class="w-4 h-4" />
            <span class="text-sm">查看详情</span>
          </button>
          <button
            @click="emit('delete', item.id)"
            class="p-2 bg-red-500/80 rounded-lg text-white hover:bg-red-500 transition-all"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>
      <div class="absolute top-3 left-3 px-3 py-1.5 bg-primary-500/90 backdrop-blur-sm rounded-full text-white text-sm font-medium">
        {{ item.total_objects }} 个目标
      </div>
    </div>
    
    <div class="p-4">
      <h3 class="text-white font-medium truncate mb-2">{{ item.filename }}</h3>
      <div class="flex items-center space-x-4 text-sm text-slate-400">
        <span class="flex items-center space-x-1">
          <Clock class="w-4 h-4" />
          <span>{{ formattedTime }}</span>
        </span>
        <span class="flex items-center space-x-1">
          <Target class="w-4 h-4" />
          <span>{{ item.model_name }}</span>
        </span>
      </div>
    </div>
  </div>
</template>
