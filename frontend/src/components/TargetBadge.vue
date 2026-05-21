<script setup lang="ts">
import { Target } from 'lucide-vue-next'
import type { TargetItem } from '@/types'

defineProps<{
  target: TargetItem
}>()
</script>

<template>
  <div class="flex items-center space-x-3 p-4 bg-slate-700/30 rounded-xl border border-slate-600/30">
    <div class="w-12 h-12 bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-xl flex items-center justify-center">
      <Target class="w-6 h-6 text-primary-400" />
    </div>
    <div>
      <h4 class="text-white font-medium">{{ target.chinese_name }}</h4>
      <p class="text-sm text-slate-400">{{ target.description }}</p>
    </div>
  </div>
</template>
