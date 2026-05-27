<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Camera, Check, Clock, AlertTriangle, Play, Pause, Video as VideoIcon, Settings, Database } from 'lucide-vue-next'
import { detectionApi, modelApi } from '@/utils/api'
import type { ModelItem } from '@/types'

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const isStreaming = ref(false)
const isDetecting = ref(false)
const detectionInterval = ref<number | null>(null)
const lastDetectionResult = ref<any>(null)
const errorMessage = ref('')
const isProcessing = ref(false)

const stream = ref<MediaStream | null>(null)

const currentModelName = ref<string>('')
const availableModels = ref<ModelItem[]>([])
const selectedModel = ref<string>('')

const confThreshold = ref(0.5)
const iouThreshold = ref(0.45)

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

const toggleStream = async () => {
  if (isStreaming.value) {
    stopStream()
  } else {
    await startStream()
  }
}

const startStream = async () => {
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'environment'
      },
      audio: false
    })

    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      videoRef.value.play()
    }

    isStreaming.value = true
    errorMessage.value = ''
  } catch (err) {
    errorMessage.value = '无法访问摄像头，请检查权限设置'
    console.error('Camera access error:', err)
  }
}

const stopStream = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  isStreaming.value = false
  stopDetection()
}

const toggleDetection = () => {
  if (isDetecting.value) {
    stopDetection()
  } else {
    startDetection()
  }
}

const startDetection = async () => {
  if (!isStreaming.value) return

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
  lastDetectionResult.value = null
  errorMessage.value = ''

  detectionInterval.value = window.setInterval(() => {
    performRealDetection()
  }, 1000)
}

const stopDetection = () => {
  if (detectionInterval.value) {
    clearInterval(detectionInterval.value)
    detectionInterval.value = null
  }
  isDetecting.value = false
}

const performRealDetection = async () => {
  if (!videoRef.value || !canvasRef.value || isProcessing.value) return

  isProcessing.value = true

  try {
    const ctx = canvasRef.value.getContext('2d')
    if (!ctx) return

    canvasRef.value.width = videoRef.value.videoWidth
    canvasRef.value.height = videoRef.value.videoHeight
    ctx.drawImage(videoRef.value, 0, 0)

    const imageData = canvasRef.value.toDataURL('image/jpeg', 0.8)
    const base64Data = imageData.split(',')[1]

    const response = await detectionApi.detectRealtime(
      base64Data,
      confThreshold.value,
      iouThreshold.value
    )

    if (response.success && response.data) {
      lastDetectionResult.value = {
        total_objects: response.data.total_objects,
        timestamp: Date.now(),
        detection_time: response.data.detection_time,
        model_name: response.data.model_name,
        boxes: response.data.boxes
      }

      drawDetectionBoxes(response.data.boxes)
    }
  } catch (error) {
    console.error('Detection error:', error)
    errorMessage.value = '检测失败，请检查后端服务'
  } finally {
    isProcessing.value = false
  }
}

const drawDetectionBoxes = (boxes: any[]) => {
  if (!canvasRef.value || !videoRef.value) return

  const ctx = canvasRef.value.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)

  const scaleX = canvasRef.value.width / videoRef.value.videoWidth
  const scaleY = canvasRef.value.height / videoRef.value.videoHeight

  boxes.forEach((box: any) => {
    ctx.strokeStyle = box.color || '#f87171'
    ctx.lineWidth = 2
    ctx.strokeRect(
      box.x1 * scaleX,
      box.y1 * scaleY,
      (box.x2 - box.x1) * scaleX,
      (box.y2 - box.y1) * scaleY
    )

    ctx.fillStyle = box.color || '#f87171'
    ctx.globalAlpha = 0.8
    ctx.font = '12px sans-serif'
    const label = `${box.chinese_name} ${(box.confidence * 100).toFixed(1)}%`
    const labelWidth = ctx.measureText(label).width

    ctx.fillRect(
      box.x1 * scaleX,
      box.y1 * scaleY - 20,
      labelWidth + 8,
      18
    )

    ctx.fillStyle = '#ffffff'
    ctx.globalAlpha = 1
    ctx.fillText(label, box.x1 * scaleX + 4, box.y1 * scaleY - 5)
  })
}

const captureAndSave = () => {
  if (!canvasRef.value || !videoRef.value) return

  const ctx = canvasRef.value.getContext('2d')
  if (ctx) {
    canvasRef.value.width = videoRef.value.videoWidth
    canvasRef.value.height = videoRef.value.videoHeight
    ctx.drawImage(videoRef.value, 0, 0)

    if (lastDetectionResult.value?.boxes?.length > 0) {
      drawDetectionBoxes(lastDetectionResult.value.boxes)
    }

    canvasRef.value.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `detection-${Date.now()}.png`
        a.click()
        URL.revokeObjectURL(url)
      }
    })
  }
}

onMounted(() => {
  loadModels()
})

onUnmounted(() => {
  stopStream()
})
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">摄像头实时检测</h1>
        <p class="text-slate-400">
          使用 {{ lastDetectionResult?.model_name || currentModelName || 'YOLO模型' }} 进行实时检测
        </p>
      </div>

      <div class="grid lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 card p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-white">视频预览</h2>
            <div class="flex items-center space-x-2">
              <Camera class="w-5 h-5 text-emerald-400" />
              <span v-if="currentModelName" class="text-sm text-slate-400">
                当前模型: {{ currentModelName }}
              </span>
            </div>
          </div>

          <div class="relative aspect-video bg-slate-900 rounded-xl overflow-hidden mb-6">
            <video
              ref="videoRef"
              class="w-full h-full object-cover"
              playsinline
            />
            <canvas
              ref="canvasRef"
              class="absolute inset-0 pointer-events-none"
            />

            <div v-if="!isStreaming" class="absolute inset-0 flex items-center justify-center bg-slate-800/90">
              <div class="text-center">
                <Camera class="w-16 h-16 mx-auto text-slate-600 mb-4" />
                <p class="text-slate-400">点击下方按钮启动摄像头</p>
              </div>
            </div>

            <div v-if="isDetecting" class="absolute top-4 right-4 px-3 py-1 bg-red-500/90 rounded-full text-white text-sm font-medium flex items-center space-x-2">
              <div class="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span>检测中</span>
            </div>
          </div>

          <div class="flex flex-wrap gap-4">
            <button
              @click="toggleStream"
              :class="isStreaming ? 'btn-secondary' : 'btn-primary'"
              class="flex items-center justify-center space-x-2"
            >
              <VideoIcon class="w-5 h-5" />
              <span>{{ isStreaming ? '关闭摄像头' : '启动摄像头' }}</span>
            </button>

            <button
              v-if="isStreaming"
              @click="toggleDetection"
              :class="isDetecting ? 'btn-secondary' : 'btn-primary'"
              class="flex items-center justify-center space-x-2"
            >
              <Play v-if="!isDetecting" class="w-5 h-5" />
              <Pause v-else class="w-5 h-5" />
              <span>{{ isDetecting ? '停止检测' : '开始检测' }}</span>
            </button>

            <button
              v-if="isStreaming"
              @click="captureAndSave"
              class="btn-secondary flex items-center justify-center space-x-2"
            >
              <Camera class="w-5 h-5" />
              <span>截图保存</span>
            </button>
          </div>

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
              </div>
            </div>
          </div>

          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
              <Settings class="w-5 h-5 text-emerald-400" />
              <span>检测参数</span>
            </h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm text-slate-400 mb-2">置信度阈值: {{ confThreshold.toFixed(2) }}</label>
                <input
                  v-model.number="confThreshold"
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>

              <div>
                <label class="block text-sm text-slate-400 mb-2">IOU阈值: {{ iouThreshold.toFixed(2) }}</label>
                <input
                  v-model.number="iouThreshold"
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>
            </div>
          </div>

          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6">实时检测结果</h2>

            <div v-if="!isDetecting && !lastDetectionResult" class="text-center py-16">
              <div class="w-20 h-20 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
                <AlertTriangle class="w-10 h-10 text-slate-500" />
              </div>
              <p class="text-slate-400">启动检测后结果将显示在这里</p>
            </div>

            <div v-else class="space-y-6">
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                  <div class="text-3xl font-bold text-emerald-400 mb-1">
                    {{ lastDetectionResult?.total_objects || 0 }}
                  </div>
                  <div class="text-sm text-slate-400">检测到目标数</div>
                </div>
                <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                  <div class="text-xl font-bold text-green-400 mb-1">
                    {{ (lastDetectionResult?.detection_time * 1000 || 0).toFixed(0) }}ms
                  </div>
                  <div class="text-sm text-slate-400">检测耗时</div>
                </div>
              </div>

              <div class="bg-slate-700/30 rounded-xl p-4">
                <h3 class="text-white font-medium mb-3">检测详情</h3>
                <div v-if="lastDetectionResult?.boxes?.length > 0" class="space-y-2 max-h-48 overflow-y-auto">
                  <div
                    v-for="(box, index) in lastDetectionResult.boxes"
                    :key="index"
                    class="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                  >
                    <div class="flex items-center space-x-3">
                      <div 
                        class="w-8 h-8 rounded-lg flex items-center justify-center text-white font-medium text-sm"
                        :style="{ backgroundColor: box.color + '40', color: box.color }"
                      >
                        {{ index + 1 }}
                      </div>
                      <div>
                        <div class="text-white text-sm">{{ box.chinese_name }}</div>
                        <div class="text-xs text-slate-400">
                          置信度: {{ (box.confidence * 100).toFixed(1) }}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="text-center py-6">
                  <Check class="w-12 h-12 mx-auto text-green-400 mb-2" />
                  <p class="text-slate-400">当前帧未检测到目标</p>
                </div>
              </div>

              <div class="flex items-center justify-between text-sm text-slate-400">
                <span class="flex items-center space-x-2">
                  <Check class="w-4 h-4 text-green-400" />
                  <span>{{ isDetecting ? '实时监控中' : '监控已停止' }}</span>
                </span>
                <span class="flex items-center space-x-2">
                  <Clock class="w-4 h-4" />
                  <span>{{ new Date().toLocaleTimeString('zh-CN') }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
