<script setup lang="ts">
import { ref, computed } from 'vue'
import { Folder, Check, Clock, AlertTriangle, Play, Pause } from 'lucide-vue-next'
import FileUploader from '@/components/FileUploader.vue'
import { detectionApi } from '@/utils/api'
import type { BatchDetectionResult } from '@/types'

const selectedFiles = ref<File[]>([])
const isDetecting = ref(false)
const result = ref<BatchDetectionResult | null>(null)
const errorMessage = ref('')
const currentIndex = ref(0)
const detectionProgress = computed(() => {
  if (!result.value || selectedFiles.value.length === 0) return 0
  return Math.round((currentIndex.value / selectedFiles.value.length) * 100)
})

const canDetect = computed(() => selectedFiles.value.length > 0 && !isDetecting.value)

const handleFilesSelected = (files: File[]) => {
  selectedFiles.value = files
  result.value = null
  errorMessage.value = ''
  currentIndex.value = 0
}

const handleClear = () => {
  selectedFiles.value = []
  result.value = null
  errorMessage.value = ''
  currentIndex.value = 0
}

const performBatchDetection = async () => {
  if (!canDetect.value) return

  isDetecting.value = true
  errorMessage.value = ''

  try {
    const response = await detectionApi.detectBatch(selectedFiles.value)

    if (response.success && response.data) {
      result.value = response.data
      currentIndex.value = selectedFiles.value.length
    } else {
      errorMessage.value = response.message || '批量检测失败'
    }
  } catch {
    errorMessage.value = '批量检测失败，请检查后端服务是否运行'
  } finally {
    isDetecting.value = false
  }
}

const getStatusColor = (success: boolean) => {
  return success ? 'text-green-400' : 'text-red-400'
}

const getStatusIcon = (success: boolean) => {
  return success ? Check : AlertTriangle
}
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">文件夹检测</h1>
        <p class="text-slate-400">批量上传多张PCB图片进行缺陷检测</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-8">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-white">上传文件</h2>
            <Folder class="w-5 h-5 text-emerald-400" />
          </div>

          <FileUploader
            multiple
            accept="image/*"
            :max-files="50"
            :max-size="200"
            label="批量上传PCB图片"
            hint="支持拖拽或点击上传，支持多个文件"
            @files="handleFilesSelected"
            @clear="handleClear"
          />

          <div class="flex flex-col sm:flex-row gap-4 mt-6">
            <button
              v-if="canDetect"
              @click="performBatchDetection"
              class="btn-primary flex items-center justify-center space-x-2"
              :disabled="isDetecting"
            >
              <Play v-if="!isDetecting" class="w-5 h-5" />
              <Pause v-else class="w-5 h-5 animate-spin" />
              <span>{{ isDetecting ? '检测中...' : '开始批量检测' }}</span>
            </button>
          </div>

          <div v-if="isDetecting" class="mt-6 space-y-4">
            <div class="flex items-center justify-between text-sm text-slate-400">
              <span>处理进度: {{ currentIndex }} / {{ selectedFiles.length }}</span>
              <span>{{ detectionProgress }}%</span>
            </div>
            <div class="w-full bg-slate-700 rounded-full h-2">
              <div
                class="bg-gradient-to-r from-emerald-500 to-green-500 h-2 rounded-full transition-all duration-300"
                :style="{ width: detectionProgress + '%' }"
              ></div>
            </div>
          </div>

          <div v-if="errorMessage" class="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
            {{ errorMessage }}
          </div>
        </div>

        <div class="card p-6">
          <h2 class="text-lg font-semibold text-white mb-6">检测结果</h2>

          <div v-if="!result" class="text-center py-16">
            <div class="w-20 h-20 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
              <AlertTriangle class="w-10 h-10 text-slate-500" />
            </div>
            <p class="text-slate-400">批量检测结果将显示在这里</p>
          </div>

          <div v-else class="space-y-6">
            <div class="grid grid-cols-3 gap-4">
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-emerald-400 mb-1">{{ result.total }}</div>
                <div class="text-sm text-slate-400">总处理数</div>
              </div>
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-green-400 mb-1">{{ result.success }}</div>
                <div class="text-sm text-slate-400">成功</div>
              </div>
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-red-400 mb-1">{{ result.failed }}</div>
                <div class="text-sm text-slate-400">失败</div>
              </div>
            </div>

            <div class="bg-slate-700/30 rounded-xl p-4">
              <h3 class="text-white font-medium mb-3">详细结果</h3>
              <div class="space-y-2 max-h-96 overflow-y-auto">
                <div
                  v-for="(item, index) in result.items"
                  :key="index"
                  class="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                >
                  <div class="flex items-center space-x-3">
                    <div
                      class="w-8 h-8 rounded-lg flex items-center justify-center"
                      :class="item.success ? 'bg-green-500/20' : 'bg-red-500/20'"
                    >
                      <component :is="getStatusIcon(item.success)" class="w-4 h-4" :class="getStatusColor(item.success)" />
                    </div>
                    <div class="min-w-0">
                      <div class="text-white text-sm truncate">{{ item.filename }}</div>
                      <div class="text-xs text-slate-400">
                        {{ item.result ? `检测到 ${item.result.total_objects} 个缺陷` : item.error || '检测失败' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex items-center justify-between text-sm text-slate-400">
              <span class="flex items-center space-x-2">
                <Check class="w-4 h-4 text-green-400" />
                <span>检测完成</span>
              </span>
              <span class="flex items-center space-x-2">
                <Clock class="w-4 h-4" />
                <span>{{ new Date().toLocaleString('zh-CN') }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
