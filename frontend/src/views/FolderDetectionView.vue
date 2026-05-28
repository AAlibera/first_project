<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Folder, Check, Clock, AlertTriangle, Play, Pause, Settings, Database } from 'lucide-vue-next'
import FileUploader from '@/components/FileUploader.vue'
import { detectionApi, modelApi } from '@/utils/api'
import type { BatchDetectionResult, ModelItem } from '@/types'

const selectedFiles = ref<File[]>([])
const isDetecting = ref(false)
const result = ref<BatchDetectionResult | null>(null)
const errorMessage = ref('')
const currentIndex = ref(0)
const availableModels = ref<ModelItem[]>([])
const selectedModel = ref<string>('')
const currentModelName = ref<string>('')

const confThreshold = ref(0.5)
const iouThreshold = ref(0.45)

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

const loadModels = async () => {
  try {
    const response = await modelApi.getList()
    if (response.success && response.data) {
      availableModels.value = response.data
    }

    const currentResponse = await modelApi.getCurrent()
    if (currentResponse.success && currentResponse.data) {
      currentModelName.value = currentResponse.data.name
      selectedModel.value = currentResponse.data.name
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const performBatchDetection = async () => {
  if (!canDetect.value) return

  isDetecting.value = true
  errorMessage.value = ''
  currentIndex.value = 0

  try {
    const response = await detectionApi.detectBatch(
      selectedFiles.value,
      selectedModel.value || undefined
    )

    if (response.success && response.data) {
      result.value = response.data
      currentIndex.value = selectedFiles.value.length
      
      const currentResponse = await modelApi.getCurrent()
      if (currentResponse.success && currentResponse.data) {
        currentModelName.value = currentResponse.data.name
      }
    } else {
      errorMessage.value = response.message || '批量检测失败'
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || '批量检测失败，请检查后端服务是否运行'
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

const getDetectionSummary = () => {
  if (!result.value || !result.value.items) return null
  
  let totalObjects = 0
  let totalTime = 0
  let successfulItems = 0
  
  result.value.items.forEach(item => {
    if (item.success && item.result) {
      totalObjects += item.result.total_objects
      totalTime += item.result.detection_time
      successfulItems++
    }
  })
  
  return {
    totalObjects,
    avgTime: successfulItems > 0 ? (totalTime / successfulItems * 1000).toFixed(0) : 0,
    totalTime: (totalTime * 1000).toFixed(0)
  }
}

onMounted(() => {
  loadModels()
})
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">文件夹批量检测</h1>
        <p class="text-slate-400">
          批量上传多张PCB图片进行缺陷检测
          <span v-if="currentModelName" class="ml-2 text-emerald-400">
            | 当前模型: {{ currentModelName }}
          </span>
        </p>
      </div>

      <div class="grid lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-6">
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
              hint="支持拖拽或点击上传，最多支持50张图像"
              @files="handleFilesSelected"
              @clear="handleClear"
            />

            <div v-if="selectedFiles.length > 0" class="mt-4 p-4 bg-slate-700/50 rounded-lg">
              <div class="flex items-center justify-between">
                <span class="text-white">已选择 {{ selectedFiles.length }} 个文件</span>
                <button @click="handleClear" class="text-sm text-red-400 hover:text-red-300">
                  清除选择
                </button>
              </div>
            </div>

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

          <div v-if="result" class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6">检测结果详情</h2>
            
            <div class="space-y-4">
              <div
                v-for="(item, index) in result.items"
                :key="index"
                class="bg-slate-700/30 rounded-xl p-4"
              >
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center space-x-3">
                    <div
                      class="w-10 h-10 rounded-lg flex items-center justify-center"
                      :class="item.success ? 'bg-green-500/20' : 'bg-red-500/20'"
                    >
                      <component 
                        :is="getStatusIcon(item.success)" 
                        class="w-5 h-5" 
                        :class="getStatusColor(item.success)" 
                      />
                    </div>
                    <div>
                      <div class="text-white font-medium">{{ item.filename }}</div>
                      <div v-if="item.success && item.result" class="text-sm text-slate-400 mt-1">
                        <span class="text-emerald-400">检测到 {{ item.result.total_objects }} 个缺陷</span>
                        <span class="mx-2">|</span>
                        <span>耗时 {{ (item.result.detection_time * 1000).toFixed(0) }}ms</span>
                      </div>
                      <div v-else-if="!item.success" class="text-sm text-red-400 mt-1">
                        {{ item.error }}
                      </div>
                    </div>
                  </div>
                  <span v-if="item.success && item.result" class="text-sm text-slate-400">
                    {{ item.result.model_name }}
                  </span>
                </div>

                <div v-if="item.success && item.result && item.result.boxes && item.result.boxes.length > 0" class="ml-13 space-y-2">
                  <div
                    v-for="(box, boxIndex) in item.result.boxes!"
                    :key="boxIndex"
                    class="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg"
                  >
                    <div class="flex items-center space-x-2">
                      <div
                        class="w-6 h-6 rounded flex items-center justify-center text-xs font-medium"
                        :style="{ backgroundColor: box.color + '40', color: box.color }"
                      >
                        {{ boxIndex + 1 }}
                      </div>
                      <span class="text-white text-sm">{{ box.chinese_name }}</span>
                    </div>
                    <span class="text-emerald-400 text-sm">
                      {{ (box.confidence * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
              <Settings class="w-5 h-5 text-emerald-400" />
              <span>检测参数</span>
            </h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm text-slate-400 mb-2">选择模型</label>
                <select
                  v-model="selectedModel"
                  class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                >
                  <option v-for="model in availableModels" :key="model.name" :value="model.name">
                    {{ model.name }}
                  </option>
                </select>
              </div>

              <div>
                <label class="block text-sm text-slate-400 mb-2">
                  置信度阈值: {{ confThreshold.toFixed(2) }}
                </label>
                <input
                  v-model.number="confThreshold"
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div class="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0.1</span>
                  <span>0.9</span>
                </div>
              </div>

              <div>
                <label class="block text-sm text-slate-400 mb-2">
                  IOU阈值: {{ iouThreshold.toFixed(2) }}
                </label>
                <input
                  v-model.number="iouThreshold"
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div class="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0.1</span>
                  <span>0.9</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
              <Database class="w-5 h-5 text-emerald-400" />
              <span>检测统计</span>
            </h2>

            <div v-if="!result" class="text-center py-8">
              <div class="w-16 h-16 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
                <AlertTriangle class="w-8 h-8 text-slate-500" />
              </div>
              <p class="text-slate-400">批量检测结果将显示在这里</p>
            </div>

            <div v-else class="space-y-4">
              <div class="grid grid-cols-3 gap-3">
                <div class="bg-slate-700/50 rounded-xl p-3 text-center">
                  <div class="text-2xl font-bold text-emerald-400">{{ result.total }}</div>
                  <div class="text-xs text-slate-400">总处理数</div>
                </div>
                <div class="bg-slate-700/50 rounded-xl p-3 text-center">
                  <div class="text-2xl font-bold text-green-400">{{ result.success }}</div>
                  <div class="text-xs text-slate-400">成功</div>
                </div>
                <div class="bg-slate-700/50 rounded-xl p-3 text-center">
                  <div class="text-2xl font-bold text-red-400">{{ result.failed }}</div>
                  <div class="text-xs text-slate-400">失败</div>
                </div>
              </div>

              <div v-if="getDetectionSummary()" class="bg-slate-700/30 rounded-xl p-4">
                <h3 class="text-white font-medium mb-3">检测摘要</h3>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-slate-400">总缺陷数:</span>
                    <span class="text-emerald-400">{{ getDetectionSummary()!.totalObjects }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-slate-400">平均耗时:</span>
                    <span class="text-blue-400">{{ getDetectionSummary()!.avgTime }}ms/张</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-slate-400">总耗时:</span>
                    <span class="text-purple-400">{{ getDetectionSummary()!.totalTime }}ms</span>
                  </div>
                </div>
              </div>

              <div class="flex items-center justify-between text-sm text-slate-400 pt-4 border-t border-slate-700">
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
  </div>
</template>
