<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Clock, Image, Trash2, RefreshCw, Eye, Target } from 'lucide-vue-next'
import { historyApi } from '@/utils/api'
import type { DetectionRecordItem } from '@/types'

const records = ref<DetectionRecordItem[]>([])
const isLoading = ref(false)
const isRefreshing = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const selectedType = ref<string | null>(null)
const selectedRecord = ref<DetectionRecordItem | null>(null)
const showDetailModal = ref(false)

const fetchRecords = async (refresh = false) => {
  if (refresh) {
    isRefreshing.value = true
  } else {
    isLoading.value = true
  }
  
  try {
    const result = await historyApi.getList(page.value, pageSize.value, selectedType.value || undefined)
    if (result.success) {
      if (page.value === 1) {
        records.value = result.data
      } else {
        records.value = [...records.value, ...result.data]
      }
      total.value = result.total
    }
  } catch (error) {
    console.error('获取历史记录失败:', error)
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

const loadMore = () => {
  if (!isLoading.value && records.value.length < total.value) {
    page.value++
    fetchRecords()
  }
}

const deleteRecord = async (recordId: string, e: MouseEvent) => {
  e.stopPropagation()
  if (!confirm('确定要删除这条记录吗？')) {
    return
  }
  
  try {
    await historyApi.delete(recordId)
    records.value = records.value.filter(r => r.id !== recordId)
    total.value--
  } catch (error) {
    console.error('删除记录失败:', error)
  }
}

const viewDetail = (record: DetectionRecordItem) => {
  selectedRecord.value = record
  showDetailModal.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedRecord.value = null
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'single': '单图检测',
    'batch': '批量检测',
    'folder': '文件夹检测',
    'video': '视频检测',
    'camera': '摄像头检测'
  }
  return labels[type] || type
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    'single': '🖼️',
    'batch': '📁',
    'folder': '📂',
    'video': '🎬',
    'camera': '📹'
  }
  return icons[type] || '📷'
}

const getStatusBadge = (status: string) => {
  const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
    'pending': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '待处理' },
    'processing': { bg: 'bg-blue-100', text: 'text-blue-800', label: '处理中' },
    'completed': { bg: 'bg-green-100', text: 'text-green-800', label: '已完成' },
    'failed': { bg: 'bg-red-100', text: 'text-red-800', label: '失败' }
  }
  return statusConfig[status] || statusConfig['pending']
}

onMounted(() => {
  fetchRecords()
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 pt-20">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 页面头部 -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h1 class="text-3xl font-bold text-white mb-2">
            <Clock class="w-8 h-8 inline mr-3 text-emerald-400" />
            检测历史
          </h1>
          <p class="text-slate-400">查看和管理您的检测记录</p>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- 筛选 -->
          <div class="flex items-center gap-2">
            <select
              v-model="selectedType"
              @change="page = 1; fetchRecords()"
              class="px-4 py-2 bg-slate-800 text-white border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option :value="null">全部类型</option>
              <option value="single">单图检测</option>
              <option value="batch">批量检测</option>
              <option value="folder">文件夹检测</option>
              <option value="video">视频检测</option>
              <option value="camera">摄像头检测</option>
            </select>
          </div>
          
          <!-- 刷新 -->
          <button
            @click="page = 1; fetchRecords(true)"
            :disabled="isRefreshing"
            class="px-4 py-2 bg-slate-800 text-white border border-slate-700 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw class="w-5 h-5 inline mr-2" :class="{ 'animate-spin': isRefreshing }" />
            刷新
          </button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div class="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm">总检测数</p>
              <p class="text-3xl font-bold text-white mt-1">{{ total }}</p>
            </div>
            <div class="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center">
              <Image class="w-6 h-6 text-emerald-400" />
            </div>
          </div>
        </div>

        <div class="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm">成功检测</p>
              <p class="text-3xl font-bold text-white mt-1">
                {{ records.filter(r => r.status === 'completed').length }}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
              <Check class="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>

        <div class="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm">检测目标</p>
              <p class="text-3xl font-bold text-white mt-1">
                {{ records.reduce((sum, r) => sum + r.total_objects, 0) }}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
              <Target class="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>
      </div>

      <!-- 记录列表 -->
      <div v-if="isLoading && records.length === 0" class="flex justify-center items-center py-20">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500"></div>
      </div>

      <div v-else-if="records.length === 0" class="bg-slate-800/30 rounded-xl p-12 text-center border border-slate-700">
        <Image class="w-16 h-16 text-slate-500 mx-auto mb-4" />
        <h3 class="text-xl font-medium text-slate-300 mb-2">暂无检测记录</h3>
        <p class="text-slate-500">开始使用检测功能后，记录将显示在这里</p>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="record in records"
          :key="record.id"
          @click="viewDetail(record)"
          class="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:bg-slate-700/50 transition-colors cursor-pointer"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-4 flex-1">
              <!-- 缩略图 -->
              <div class="w-20 h-20 bg-slate-700 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
                <img
                  v-if="record.result_image_url"
                  :src="record.result_image_url"
                  :alt="record.id"
                  class="w-full h-full object-cover"
                  @error="($event.target as HTMLImageElement).style.display = 'none'"
                />
                <span v-else class="text-3xl">{{ getTypeIcon(record.type) }}</span>
              </div>
              
              <!-- 记录信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-lg font-medium text-white">{{ getTypeLabel(record.type) }}</span>
                  <span
                    :class="['px-2 py-0.5 rounded-full text-xs font-medium', getStatusBadge(record.status).bg, getStatusBadge(record.status).text]"
                  >
                    {{ getStatusBadge(record.status).label }}
                  </span>
                </div>
                
                <div class="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-400">
                  <span class="flex items-center gap-1">
                    <Image class="w-3 h-3" />
                    {{ record.model_name }}
                  </span>
                  <span class="flex items-center gap-1">
                    <Target class="w-3 h-3" />
                    {{ record.total_objects }} 个目标
                  </span>
                  <span v-if="record.detection_time" class="flex items-center gap-1">
                    <Clock class="w-3 h-3" />
                    {{ record.detection_time.toFixed(2) }}s
                  </span>
                </div>
                
                <p class="text-xs text-slate-500 mt-1">{{ formatDate(record.created_at) }}</p>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex items-center gap-2 flex-shrink-0">
              <button
                @click.stop="viewDetail(record)"
                class="p-2 text-slate-400 hover:text-white hover:bg-slate-600 rounded-lg transition-colors"
                title="查看详情"
              >
                <Eye class="w-5 h-5" />
              </button>
              <button
                @click="deleteRecord(record.id, $event)"
                class="p-2 text-slate-400 hover:text-red-400 hover:bg-red-900/30 rounded-lg transition-colors"
                title="删除"
              >
                <Trash2 class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="records.length < total" class="text-center">
          <button
            @click="loadMore"
            :disabled="isLoading"
            class="px-6 py-3 bg-slate-800 text-white border border-slate-700 rounded-xl hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            {{ isLoading ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 详情模态框 -->
    <div v-if="showDetailModal && selectedRecord" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div class="bg-slate-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div class="sticky top-0 bg-slate-900 border-b border-slate-700 p-6 flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
              {{ getTypeIcon(selectedRecord.type) }}
              {{ getTypeLabel(selectedRecord.type) }} 详情
            </h2>
            <p class="text-slate-400 text-sm">{{ formatDate(selectedRecord.created_at) }}</p>
          </div>
          <button
            @click="closeDetailModal"
            class="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="p-6">
          <!-- 图片展示 -->
          <div v-if="selectedRecord.result_image_url" class="mb-6">
            <img
              :src="selectedRecord.result_image_url"
              alt="检测结果"
              class="w-full rounded-xl bg-slate-800"
            />
          </div>
          
          <!-- 检测框列表 -->
          <div v-if="selectedRecord.boxes && selectedRecord.boxes.length > 0" class="mt-6">
            <h3 class="text-lg font-semibold text-white mb-4">检测到的目标 ({{ selectedRecord.boxes.length }})</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <div
                v-for="(box, idx) in selectedRecord.boxes"
                :key="idx"
                class="bg-slate-800 rounded-lg p-4 border border-slate-700"
              >
                <div class="flex items-center justify-between mb-2">
                  <span
                    class="px-2 py-1 rounded-full text-xs font-medium"
                    :style="{ backgroundColor: box.color || '#10b981', color: '#fff' }"
                  >
                    {{ box.chinese_name || box.class_name }}
                  </span>
                  <span class="text-xs text-slate-400">
                    {{ (box.confidence * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="text-sm text-slate-500">
                  坐标: [{{ box.x1.toFixed(0) }}, {{ box.y1.toFixed(0) }}, {{ box.x2.toFixed(0) }}, {{ box.y2.toFixed(0) }}]
                </div>
              </div>
            </div>
          </div>
          
          <!-- 基本信息 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-700">
            <div class="text-sm">
              <span class="text-slate-500">使用模型:</span>
              <span class="text-white ml-2">{{ selectedRecord.model_name }}</span>
            </div>
            <div class="text-sm">
              <span class="text-slate-500">检测状态:</span>
              <span
                :class="['ml-2 px-2 py-0.5 rounded-full text-xs font-medium', getStatusBadge(selectedRecord.status).bg, getStatusBadge(selectedRecord.status).text]"
              >
                {{ getStatusBadge(selectedRecord.status).label }}
              </span>
            </div>
            <div class="text-sm">
              <span class="text-slate-500">目标总数:</span>
              <span class="text-white ml-2">{{ selectedRecord.total_objects }}</span>
            </div>
            <div v-if="selectedRecord.detection_time" class="text-sm">
              <span class="text-slate-500">检测耗时:</span>
              <span class="text-white ml-2">{{ selectedRecord.detection_time.toFixed(2) }}s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
