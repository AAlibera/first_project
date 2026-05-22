<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next'
import type { TargetItem } from '@/types'

const props = defineProps<{
  target: TargetItem
}>()
</script>

<template>
  <div class="flex items-center space-x-3 p-4 bg-slate-700/30 rounded-xl border border-slate-600/30">
    <div
      class="w-12 h-12 rounded-xl flex items-center justify-center"
      :style="{ backgroundColor: target.color + '30' }"
    >
      <AlertTriangle class="w-6 h-6" :style="{ color: target.color }" />
    </div>
    <div>
      <h4 class="text-white font-medium">{{ target.chinese_name }}</h4>
      <p class="text-sm text-slate-400">{{ target.description }}</p>
    </div>
  </div>
</template>