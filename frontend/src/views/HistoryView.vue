<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { History, Trash2, Eye, RefreshCw, ImageOff } from 'lucide-vue-next'
import DetectionCard from '@/components/DetectionCard.vue'
import { detectionApi } from '@/utils/api'
import type { HistoryItem } from '@/types'

const historyItems = ref<HistoryItem[]>([])
const isLoading = ref(true)
const isRefreshing = ref(false)

const loadHistory = async () => {
  isLoading.value = true
  try {
    const response = await detectionApi.getHistory()
    if (response.success) {
      historyItems.value = response.data
    }
  } catch {
    historyItems.value = []
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

const handleView = (id: string) => {
  console.log('View detection:', id)
}

const handleDelete = async (id: string) => {
  if (!confirm('确定要删除这条记录吗？')) return
  
  try {
    const response = await detectionApi.deleteDetection(id)
    if (response.success) {
      historyItems.value = historyItems.value.filter(item => item.id !== id)
    }
  } catch {
    alert('删除失败')
  }
}

const handleRefresh = () => {
  isRefreshing.value = true
  loadHistory()
}

onMounted(loadHistory)
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-white mb-2">检测历史记录</h1>
          <p class="text-slate-400">查看和管理您的检测记录</p>
        </div>
        <button
          @click="handleRefresh"
          :disabled="isRefreshing"
          class="btn-secondary flex items-center space-x-2 mt-4 sm:mt-0"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" />
          <span>刷新</span>
        </button>
      </div>
      
      <div v-if="isLoading" class="text-center py-16">
        <div class="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-slate-400">加载中...</p>
      </div>
      
      <div v-else-if="historyItems.length === 0" class="text-center py-16">
        <div class="w-20 h-20 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
          <History class="w-10 h-10 text-slate-500" />
        </div>
        <h3 class="text-xl font-medium text-white mb-2">暂无检测记录</h3>
        <p class="text-slate-400">上传图片进行检测后，记录将显示在这里</p>
      </div>
      
      <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <DetectionCard
          v-for="item in historyItems"
          :key="item.id"
          :item="item"
          @view="handleView"
          @delete="handleDelete"
        />
      </div>
      
      <div v-if="historyItems.length > 0" class="mt-8 text-center text-slate-400 text-sm">
        共 {{ historyItems.length }} 条记录
      </div>
    </div>
  </div>
</template>
