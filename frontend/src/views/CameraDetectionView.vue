<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Camera, Check, Clock, AlertTriangle, Play, Pause, Video as VideoIcon } from 'lucide-vue-next'

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const isStreaming = ref(false)
const isDetecting = ref(false)
const detectionInterval = ref<number | null>(null)
const lastDetectionResult = ref<any>(null)
const errorMessage = ref('')

const stream = ref<MediaStream | null>(null)

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

const startDetection = () => {
  if (!isStreaming.value) return

  isDetecting.value = true
  lastDetectionResult.value = null

  // Simulate real-time detection
  detectionInterval.value = window.setInterval(() => {
    performSimulatedDetection()
  }, 1000)
}

const stopDetection = () => {
  if (detectionInterval.value) {
    clearInterval(detectionInterval.value)
    detectionInterval.value = null
  }
  isDetecting.value = false
}

const performSimulatedDetection = () => {
  // Simulate detection results
  const randomCount = Math.floor(Math.random() * 5)
  lastDetectionResult.value = {
    total_objects: randomCount,
    timestamp: Date.now(),
    boxes: randomCount > 0 ? Array(randomCount).fill(0).map(() => ({
      class_id: Math.floor(Math.random() * 6),
      chinese_name: ['划痕', '裂纹', '孔洞', '变形', '缺失', '焊点异常'][Math.floor(Math.random() * 6)],
      confidence: 0.7 + Math.random() * 0.3
    })) : []
  }
}

const captureAndSave = () => {
  if (!canvasRef.value || !videoRef.value) return

  const ctx = canvasRef.value.getContext('2d')
  if (ctx) {
    canvasRef.value.width = videoRef.value.videoWidth
    canvasRef.value.height = videoRef.value.videoHeight
    ctx.drawImage(videoRef.value, 0, 0)

    canvasRef.value.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `pcb-detection-${Date.now()}.png`
        a.click()
        URL.revokeObjectURL(url)
      }
    })
  }
}

onMounted(() => {
  // Optional: auto-start camera
  // startStream()
})

onUnmounted(() => {
  stopStream()
})
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">摄像头检测</h1>
        <p class="text-slate-400">使用摄像头实时检测PCB缺陷</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-8">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-white">视频预览</h2>
            <Camera class="w-5 h-5 text-emerald-400" />
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
          </div>

          <div class="flex gap-4">
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
                <div class="text-sm text-slate-400">当前缺陷数</div>
              </div>
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-green-400 mb-1">
                  {{ isDetecting ? '检测中' : '已停止' }}
                </div>
                <div class="text-sm text-slate-400">状态</div>
              </div>
            </div>

            <div class="bg-slate-700/30 rounded-xl p-4">
              <h3 class="text-white font-medium mb-3">检测详情</h3>
              <div v-if="lastDetectionResult?.boxes?.length > 0" class="space-y-2">
                <div
                  v-for="(box, index) in lastDetectionResult.boxes"
                  :key="index"
                  class="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                >
                  <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400 font-medium">
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
                <p class="text-slate-400">当前帧未检测到缺陷</p>
              </div>
            </div>

            <div class="flex items-center justify-between text-sm text-slate-400">
              <span class="flex items-center space-x-2">
                <Check class="w-4 h-4 text-green-400" />
                <span>实时监控中</span>
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