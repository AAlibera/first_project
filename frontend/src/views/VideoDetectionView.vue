<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  Check, Clock, Play, Pause, 
  Upload, Settings, Monitor, Database, StopCircle 
} from 'lucide-vue-next'
import FileUploader from '@/components/FileUploader.vue'
import { detectionApi, modelApi } from '@/utils/api'
import type { DetectionBox, ModelItem } from '@/types'

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const overlayCanvasRef = ref<HTMLCanvasElement | null>(null)

const selectedVideoFile = ref<File | null>(null)
const videoUrl = ref<string>('')
const isPlaying = ref(false)
const isDetecting = ref(false)
const isPaused = ref(false)
const isProcessing = ref(false)
const isVideoLoaded = ref(false)

const currentModelName = ref<string>('')
const availableModels = ref<ModelItem[]>([])
const selectedModel = ref<string>('')

const confThreshold = ref(0.5)
const iouThreshold = ref(0.45)
const detectionInterval = ref(1000)

const errorMessage = ref('')
const currentFrameIndex = ref(0)
const totalFramesProcessed = ref(0)
const totalObjectsDetected = ref(0)
const totalDetectionTime = ref(0)

const currentBoxes = ref<DetectionBox[]>([])
const lastBoxes = ref<DetectionBox[]>([])

const animationFrameId = ref<number | null>(null)
const detectionTimerId = ref<number | null>(null)

const canPlay = computed(() => selectedVideoFile.value !== null)
const canDetect = computed(() => canPlay.value && !isDetecting.value && !isProcessing.value)

const averageDetectionTime = computed(() => {
  if (totalFramesProcessed.value === 0) return 0
  return (totalDetectionTime.value / totalFramesProcessed.value * 1000).toFixed(1)
})

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

const handleFilesSelected = (files: File[]) => {
  if (files.length > 0) {
    selectedVideoFile.value = files[0]
    videoUrl.value = URL.createObjectURL(files[0])
    isVideoLoaded.value = false
    resetDetectionState()
  }
}

const handleClear = () => {
  stopDetection()
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value)
  }
  selectedVideoFile.value = null
  videoUrl.value = ''
  resetDetectionState()
}

const resetDetectionState = () => {
  currentFrameIndex.value = 0
  totalFramesProcessed.value = 0
  totalObjectsDetected.value = 0
  totalDetectionTime.value = 0
  currentBoxes.value = []
  lastBoxes.value = []
  errorMessage.value = ''
}

const togglePlay = () => {
  if (!videoRef.value) return
  
  if (isPlaying.value) {
    videoRef.value.pause()
    isPaused.value = true
  } else {
    videoRef.value.play()
    isPaused.value = false
  }
  isPlaying.value = !isPlaying.value
}

const resizeOverlayCanvas = () => {
  if (!videoRef.value || !overlayCanvasRef.value) return
  
  const rect = videoRef.value.getBoundingClientRect()
  overlayCanvasRef.value.width = rect.width
  overlayCanvasRef.value.height = rect.height
}

const drawBoxes = (boxes: DetectionBox[]) => {
  if (!overlayCanvasRef.value || !videoRef.value) return
  
  const ctx = overlayCanvasRef.value.getContext('2d')
  if (!ctx) return
  
  ctx.clearRect(0, 0, overlayCanvasRef.value.width, overlayCanvasRef.value.height)
  
  if (boxes.length === 0) return
  
  const videoRect = videoRef.value.getBoundingClientRect()
  const videoWidth = videoRef.value.videoWidth || videoRect.width
  const videoHeight = videoRef.value.videoHeight || videoRect.height
  
  const scaleX = videoRect.width / videoWidth
  const scaleY = videoRect.height / videoHeight
  
  boxes.forEach(box => {
    const x1 = box.x1 * scaleX
    const y1 = box.y1 * scaleY
    const width = (box.x2 - box.x1) * scaleX
    const height = (box.y2 - box.y1) * scaleY
    
    ctx.strokeStyle = box.color
    ctx.lineWidth = 3
    ctx.strokeRect(x1, y1, width, height)
    
    ctx.fillStyle = box.color
    ctx.globalAlpha = 0.8
    const label = `${box.chinese_name} ${(box.confidence * 100).toFixed(1)}%`
    const labelWidth = ctx.measureText(label).width + 12
    ctx.fillRect(x1, y1 - 20, labelWidth, 18)
    
    ctx.fillStyle = '#ffffff'
    ctx.globalAlpha = 1
    ctx.font = '12px sans-serif'
    ctx.fillText(label, x1 + 6, y1 - 6)
  })
}

const captureAndDetectFrame = async () => {
  if (!videoRef.value || !canvasRef.value || isProcessing.value || !isVideoLoaded.value) return
  
  // 等待视频元数据加载
  if (!videoRef.value.videoWidth || !videoRef.value.videoHeight) {
    console.warn('视频未加载完成，等待中...')
    // 尝试等待视频准备好
    await new Promise<void>((resolve) => {
      const checkVideo = () => {
        if (videoRef.value && videoRef.value.videoWidth > 0 && videoRef.value.videoHeight > 0) {
          resolve()
        } else {
          setTimeout(checkVideo, 50)
        }
      }
      checkVideo()
    })
    
    // 再次检查，如果还没准备好就跳过
    if (!videoRef.value.videoWidth || !videoRef.value.videoHeight) {
      console.warn('视频未加载完成，跳过此帧')
      return
    }
  }
  
  isProcessing.value = true
  
  try {
    const ctx = canvasRef.value.getContext('2d')
    if (!ctx) {
      console.error('无法获取 canvas context')
      isProcessing.value = false
      return
    }
    
    canvasRef.value.width = videoRef.value.videoWidth
    canvasRef.value.height = videoRef.value.videoHeight
    
    if (canvasRef.value.width === 0 || canvasRef.value.height === 0) {
      console.warn('Canvas 尺寸为 0，跳过此帧')
      isProcessing.value = false
      return
    }
    
    ctx.drawImage(videoRef.value, 0, 0)
    
    const imageData = canvasRef.value.toDataURL('image/jpeg', 0.7)
    
    if (!imageData || !imageData.includes(',')) {
      console.error('无法获取图片数据')
      isProcessing.value = false
      return
    }
    
    const base64Data = imageData.split(',')[1]
    
    if (!base64Data || base64Data.length === 0) {
      console.error('Base64 数据为空')
      isProcessing.value = false
      return
    }
    
    const response = await detectionApi.detectRealtime(
      base64Data,
      confThreshold.value,
      iouThreshold.value
    )
    
    if (response.success && response.data) {
      currentBoxes.value = response.data.boxes
      lastBoxes.value = response.data.boxes
      
      totalFramesProcessed.value++
      totalObjectsDetected.value += response.data.total_objects
      totalDetectionTime.value += response.data.detection_time
      
      if (response.data.model_name) {
        currentModelName.value = response.data.model_name
      }
      
      drawBoxes(currentBoxes.value)
    }
  } catch (error: any) {
    console.error('检测失败:', error)
    errorMessage.value = error.response?.data?.detail || '检测失败'
  } finally {
    isProcessing.value = false
  }
}

const animationLoop = () => {
  if (lastBoxes.value.length > 0) {
    drawBoxes(lastBoxes.value)
  }
  
  animationFrameId.value = requestAnimationFrame(animationLoop)
}

const startDetection = async () => {
  if (!canDetect.value || !videoRef.value) return
  
  if (selectedModel.value && selectedModel.value !== currentModelName.value) {
    try {
      await modelApi.switchModel(selectedModel.value)
      const currentResponse = await modelApi.getCurrent()
      if (currentResponse.success && currentResponse.data) {
        currentModelName.value = currentResponse.data.name
      }
    } catch (error) {
      console.error('切换模型失败:', error)
    }
  }
  
  isDetecting.value = true
  errorMessage.value = ''
  
  // 等待视频完全准备好
  await new Promise<void>((resolve) => {
    const checkReady = () => {
      if (videoRef.value && videoRef.value.videoWidth > 0 && videoRef.value.videoHeight > 0) {
        resolve()
      } else {
        setTimeout(checkReady, 100)
      }
    }
    checkReady()
  })
  
  if (!isPlaying.value) {
    videoRef.value.play()
    isPlaying.value = true
    isPaused.value = false
  }
  
  resizeOverlayCanvas()
  
  animationLoop()
  
  await captureAndDetectFrame()
  
  detectionTimerId.value = window.setInterval(() => {
    if (isDetecting.value && !isPaused.value) {
      captureAndDetectFrame()
    }
  }, detectionInterval.value)
}

const stopDetection = () => {
  isDetecting.value = false
  
  if (detectionTimerId.value) {
    clearInterval(detectionTimerId.value)
    detectionTimerId.value = null
  }
  
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value)
    animationFrameId.value = null
  }
}

const handleVideoCanPlay = () => {
  isVideoLoaded.value = true
  resizeOverlayCanvas()
  console.log('视频加载成功，可以播放')
}

const handleVideoLoaded = () => {
  console.log('视频元数据加载完成', {
    width: videoRef.value?.videoWidth,
    height: videoRef.value?.videoHeight
  })
  isVideoLoaded.value = true
  resizeOverlayCanvas()
}

const handleVideoError = (event: Event) => {
  const video = event.target as HTMLVideoElement
  console.error('视频加载失败:', video.error)
  errorMessage.value = '视频加载失败，请尝试其他格式（推荐 MP4 格式）'
}

onMounted(() => {
  loadModels()
  window.addEventListener('resize', resizeOverlayCanvas)
})

onUnmounted(() => {
  stopDetection()
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value)
  }
  window.removeEventListener('resize', resizeOverlayCanvas)
})
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">视频实时检测</h1>
        <p class="text-slate-400">
          使用 {{ currentModelName || 'YOLO模型' }} 进行实时视频缺陷检测
        </p>
      </div>

      <div class="grid lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-6">
          <div class="card p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-lg font-semibold text-white">视频播放</h2>
              <Monitor class="w-5 h-5 text-emerald-400" />
            </div>

            <div v-if="!videoUrl" class="mb-6">
              <FileUploader
                :multiple="false"
                accept="video/*"
                :max-files="1"
                :max-size="500"
                label="上传PCB检测视频"
                hint="支持拖拽或点击上传，支持 MP4, AVI, MOV 等格式"
                @files="handleFilesSelected"
                @clear="handleClear"
              />
            </div>

            <div v-else class="relative aspect-video bg-black rounded-xl overflow-hidden mb-6">
              <video
                ref="videoRef"
                :src="videoUrl"
                class="w-full h-full object-contain"
                @error="handleVideoError"
                @canplay="handleVideoCanPlay"
                @loadedmetadata="handleVideoLoaded"
                @play="isPlaying = true"
                @pause="isPlaying = false"
                crossorigin="anonymous"
                preload="metadata"
              />
              
              <canvas
                ref="overlayCanvasRef"
                class="absolute top-0 left-0 w-full h-full pointer-events-none z-10"
              />
              
              <canvas
                ref="canvasRef"
                class="hidden"
              />

              <div v-if="!isPlaying && videoUrl" class="absolute inset-0 flex items-center justify-center bg-black/50 z-20">
                <button
                  @click="togglePlay"
                  class="w-20 h-20 rounded-full bg-emerald-500/80 hover:bg-emerald-500 flex items-center justify-center transition-all"
                >
                  <Play class="w-10 h-10 text-white ml-1" />
                </button>
              </div>
            </div>

            <div v-if="videoUrl" class="flex flex-wrap gap-4">
              <button
                @click="togglePlay"
                class="btn-secondary flex items-center justify-center space-x-2"
              >
                <Play v-if="!isPlaying" class="w-5 h-5" />
                <Pause v-else class="w-5 h-5" />
                <span>{{ isPlaying ? '暂停视频' : '播放视频' }}</span>
              </button>

              <button
                v-if="canDetect"
                @click="startDetection"
                class="btn-primary flex items-center justify-center space-x-2"
                :disabled="isDetecting"
              >
                <Play class="w-5 h-5" />
                <span>开始实时检测</span>
              </button>

              <button
                v-if="isDetecting"
                @click="stopDetection"
                class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg flex items-center justify-center space-x-2"
              >
                <StopCircle class="w-5 h-5" />
                <span>停止检测</span>
              </button>

              <button
                @click="handleClear"
                class="btn-secondary flex items-center justify-center space-x-2"
              >
                <Upload class="w-5 h-5" />
                <span>重新上传</span>
              </button>
            </div>

            <div v-if="errorMessage" class="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
              {{ errorMessage }}
            </div>
          </div>

          <div v-if="totalFramesProcessed > 0" class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6">实时检测结果</h2>
            
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-slate-700/50 rounded-xl p-4">
                  <div class="text-3xl font-bold text-emerald-400">{{ totalFramesProcessed }}</div>
                  <div class="text-sm text-slate-400">已处理帧数</div>
                </div>
                <div class="bg-slate-700/50 rounded-xl p-4">
                  <div class="text-3xl font-bold text-yellow-400">{{ totalObjectsDetected }}</div>
                  <div class="text-sm text-slate-400">检测到的缺陷</div>
                </div>
              </div>

              <div class="bg-slate-700/30 rounded-xl p-4">
                <h3 class="text-white font-medium mb-3">当前帧检测</h3>
                <div v-if="currentBoxes.length > 0" class="space-y-2 max-h-48 overflow-y-auto">
                  <div
                    v-for="(box, index) in currentBoxes"
                    :key="index"
                    class="flex items-center justify-between p-2 bg-slate-700/50 rounded-lg"
                  >
                    <div class="flex items-center space-x-2">
                      <div
                        class="w-6 h-6 rounded flex items-center justify-center text-xs font-medium"
                        :style="{ backgroundColor: box.color + '40', color: box.color }"
                      >
                        {{ index + 1 }}
                      </div>
                      <span class="text-white text-sm">{{ box.chinese_name }}</span>
                    </div>
                    <span class="text-emerald-400 text-sm">
                      {{ (box.confidence * 100).toFixed(1) }}%
                    </span>
                  </div>
                </div>
                <div v-else class="text-center py-4">
                  <Check class="w-8 h-8 mx-auto text-green-400 mb-2" />
                  <p class="text-slate-400">当前帧未检测到缺陷</p>
                </div>
              </div>

              <div class="flex items-center justify-between text-sm text-slate-400">
                <span class="flex items-center space-x-2">
                  <Check class="w-4 h-4 text-green-400" />
                  <span>{{ isDetecting ? '实时检测中' : '检测已停止' }}</span>
                </span>
                <span class="flex items-center space-x-2">
                  <Clock class="w-4 h-4" />
                  <span>平均: {{ averageDetectionTime }}ms/帧</span>
                </span>
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

              <div>
                <label class="block text-sm text-slate-400 mb-2">
                  检测间隔: {{ detectionInterval }}ms
                </label>
                <input
                  v-model.number="detectionInterval"
                  type="range"
                  min="200"
                  max="3000"
                  step="100"
                  class="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div class="flex justify-between text-xs text-slate-500 mt-1">
                  <span>200ms</span>
                  <span>3000ms</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card p-6">
            <h2 class="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
              <Database class="w-5 h-5 text-emerald-400" />
              <span>统计信息</span>
            </h2>

            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-3">
                <div class="bg-slate-700/50 rounded-xl p-3 text-center">
                  <div class="text-xl font-bold text-emerald-400">{{ totalFramesProcessed }}</div>
                  <div class="text-xs text-slate-400">处理帧数</div>
                </div>
                <div class="bg-slate-700/50 rounded-xl p-3 text-center">
                  <div class="text-xl font-bold text-yellow-400">{{ totalObjectsDetected }}</div>
                  <div class="text-xs text-slate-400">总缺陷数</div>
                </div>
              </div>

              <div class="bg-slate-700/30 rounded-xl p-4">
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-slate-400">当前模型:</span>
                    <span class="text-white">{{ currentModelName }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-slate-400">平均耗时:</span>
                    <span class="text-blue-400">{{ averageDetectionTime }}ms/帧</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-slate-400">总耗时:</span>
                    <span class="text-purple-400">{{ (totalDetectionTime * 1000).toFixed(0) }}ms</span>
                  </div>
                </div>
              </div>

              <div class="text-xs text-slate-500 text-center">
                提示: 检测间隔越短，实时性越好，但性能消耗越大
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
