<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Upload, Camera, RefreshCw, Check, Clock, AlertTriangle, X, Database } from 'lucide-vue-next'
import { detectionApi, modelApi } from '@/utils/api'
import type { DetectionResult, DetectionBox, ModelItem } from '@/types'

const currentModelName = ref<string>('')
const availableModels = ref<ModelItem[]>([])
const selectedModel = ref<string>('')

const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const isDetecting = ref(false)
const result = ref<DetectionResult | null>(null)
const errorMessage = ref('')
const detectedBoxes = ref<DetectionBox[]>([])

const imageRef = ref<HTMLImageElement | null>(null)
const boxContainerRef = ref<HTMLDivElement | null>(null)
const imageWidth = ref(0)
const imageHeight = ref(0)

const canDetect = computed(() => selectedFile.value && !isDetecting.value)

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    if (!file.type.startsWith('image/')) {
      errorMessage.value = '请选择有效的图片文件'
      return
    }

    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
    result.value = null
    errorMessage.value = ''
    detectedBoxes.value = []
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const file = event.dataTransfer?.files?.[0]

  if (file) {
    if (!file.type.startsWith('image/')) {
      errorMessage.value = '请选择有效的图片文件'
      return
    }

    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
    result.value = null
    errorMessage.value = ''
    detectedBoxes.value = []
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const handleImageLoad = () => {
  if (imageRef.value) {
    imageWidth.value = imageRef.value.naturalWidth
    imageHeight.value = imageRef.value.naturalHeight
  }
}

const performDetection = async () => {
  if (!selectedFile.value) return

  if (selectedModel.value && selectedModel.value !== currentModelName.value) {
    try {
      await modelApi.switchModel(selectedModel.value)
      const currentResponse = await modelApi.getCurrent()
      if (currentResponse.success && currentResponse.data) {
        currentModelName.value = currentResponse.data.name
      }
    } catch (error) {
      console.error('切换模型失败:', error)
      errorMessage.value = '切换模型失败'
      return
    }
  }

  isDetecting.value = true
  errorMessage.value = ''

  try {
    const response = await detectionApi.detectSingle(selectedFile.value, selectedModel.value || undefined)

    if (response.success && response.data) {
      result.value = response.data
      detectedBoxes.value = response.data.boxes
      previewUrl.value = response.data.result_image_url
    } else {
      errorMessage.value = response.message || '检测失败'
    }
  } catch {
    errorMessage.value = '检测失败，请检查后端服务是否运行'
  } finally {
    isDetecting.value = false
  }
}

const clearSelection = () => {
  selectedFile.value = null
  previewUrl.value = ''
  result.value = null
  errorMessage.value = ''
  detectedBoxes.value = []
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

onMounted(() => {
  loadModels()
})

const getBoxStyle = (box: DetectionBox) => {
  const scaleX = (boxContainerRef.value?.clientWidth || 400) / imageWidth.value
  const scaleY = (boxContainerRef.value?.clientHeight || 400) / imageHeight.value

  return {
    left: `${box.x1 * scaleX}px`,
    top: `${box.y1 * scaleY}px`,
    width: `${(box.x2 - box.x1) * scaleX}px`,
    height: `${(box.y2 - box.y1) * scaleY}px`,
    borderColor: box.color,
    backgroundColor: box.color + '20'
  }
}

const getBoxLabelStyle = (box: DetectionBox) => {
  return {
    backgroundColor: box.color,
    color: '#0f172a'
  }
}
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">单图检测</h1>
        <p class="text-slate-400">上传PCB图片进行缺陷检测</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-8">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-white">上传图片</h2>
            <button
              v-if="selectedFile"
              @click="clearSelection"
              class="p-2 text-slate-400 hover:text-red-400 transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <div
            v-if="!previewUrl"
            class="border-2 border-dashed border-slate-600 rounded-xl p-12 text-center hover:border-emerald-500 transition-colors cursor-pointer"
            @click="$refs.fileInput?.click()"
            @drop="handleDrop"
            @dragover="handleDragOver"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileSelect"
            />
            <div class="w-20 h-20 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
              <Upload class="w-10 h-10 text-slate-400" />
            </div>
            <p class="text-white font-medium mb-2">点击或拖拽上传图片</p>
            <p class="text-slate-400 text-sm">支持 JPG, PNG, BMP 等格式</p>
          </div>

          <div v-else class="relative">
            <div
              ref="boxContainer"
              class="relative rounded-xl overflow-hidden bg-slate-900"
            >
              <img
                ref="imageRef"
                :src="previewUrl"
                alt="Preview"
                class="w-full h-auto"
                @load="handleImageLoad"
              />
              <div
                v-for="(box, index) in detectedBoxes"
                :key="index"
                class="detection-box"
                :style="getBoxStyle(box)"
              >
                <div class="detection-label" :style="getBoxLabelStyle(box)">
                  {{ box.chinese_name }} {{ (box.confidence * 100).toFixed(0) }}%
                </div>
              </div>
            </div>

            <div class="mt-4 flex items-center space-x-2 text-slate-400 text-sm">
              <Camera class="w-4 h-4" />
              <span>{{ selectedFile?.name }}</span>
            </div>
          </div>

          <button
            v-if="canDetect"
            @click="performDetection"
            class="w-full mt-6 btn-primary flex items-center justify-center space-x-2"
          >
            <Camera v-if="!isDetecting" class="w-5 h-5" />
            <RefreshCw v-else class="w-5 h-5 animate-spin" />
            <span>{{ isDetecting ? '检测中...' : '开始检测' }}</span>
          </button>

          <div v-if="errorMessage" class="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
            {{ errorMessage }}
          </div>
        </div>

        <div class="space-y-6">
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
              <Database class="w-5 h-5 text-emerald-400" />
              <span>模型选择</span>
            </h2>

            <div class="space-y-4">
              <div>
                <label class="block text-sm text-slate-400 mb-2">选择检测模型</label>
                <select
                  v-model="selectedModel"
                  class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                >
                  <option v-for="model in availableModels" :key="model.name" :value="model.name">
                    {{ model.name }}
                  </option>
                </select>
                <p class="text-xs text-slate-500 mt-2">当前使用: {{ currentModelName || '未加载' }}</p>
              </div>
            </div>
          </div>

          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6">检测结果</h2>

          <div v-if="!result" class="text-center py-16">
            <div class="w-20 h-20 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
              <AlertTriangle class="w-10 h-10 text-slate-500" />
            </div>
            <p class="text-slate-400">检测结果将显示在这里</p>
          </div>

          <div v-else class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-emerald-400 mb-1">{{ result.total_objects }}</div>
                <div class="text-sm text-slate-400">检测缺陷数</div>
              </div>
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-emerald-400 mb-1">{{ result.detection_time.toFixed(3) }}s</div>
                <div class="text-sm text-slate-400">检测耗时</div>
              </div>
            </div>

            <div class="bg-slate-700/30 rounded-xl p-4">
              <h3 class="text-white font-medium mb-3">缺陷详情</h3>
              <div v-if="result.boxes.length > 0" class="space-y-2">
                <div
                  v-for="(box, index) in result.boxes"
                  :key="index"
                  class="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                >
                  <div class="flex items-center space-x-3">
                    <div
                      class="w-8 h-8 rounded-lg flex items-center justify-center"
                      :style="{ backgroundColor: box.color + '30', color: box.color }"
                    >
                      {{ index + 1 }}
                    </div>
                    <div>
                      <div class="text-white font-medium">{{ box.chinese_name }}</div>
                      <div class="text-xs text-slate-400">置信度: {{ (box.confidence * 100).toFixed(1) }}%</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-8">
                <Check class="w-12 h-12 mx-auto text-green-400 mb-2" />
                <p class="text-slate-400">未检测到缺陷，品质良好</p>
              </div>
            </div>

            <div class="flex items-center justify-between text-sm text-slate-400">
              <span class="flex items-center space-x-2">
                <Check class="w-4 h-4 text-green-400" />
                <span>检测完成</span>
              </span>
              <span class="flex items-center space-x-2">
                <Clock class="w-4 h-4" />
                <span>{{ new Date(result.created_at).toLocaleString('zh-CN') }}</span>
              </span>
            </div>
          </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>