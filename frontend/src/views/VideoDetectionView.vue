<script setup lang="ts">
import { ref, computed } from 'vue'
import { Video, Check, Clock, AlertTriangle, Play, Pause } from 'lucide-vue-next'
import FileUploader from '@/components/FileUploader.vue'
import { detectionApi } from '@/utils/api'
import type { VideoDetectionResult } from '@/types'

const selectedFiles = ref<File[]>([])
const isDetecting = ref(false)
const result = ref<VideoDetectionResult | null>(null)
const errorMessage = ref('')

const canDetect = computed(() => selectedFiles.value.length > 0 && !isDetecting.value)

const handleFilesSelected = (files: File[]) => {
  selectedFiles.value = files
  result.value = null
  errorMessage.value = ''
}

const handleClear = () => {
  selectedFiles.value = []
  result.value = null
  errorMessage.value = ''
}

const performVideoDetection = async () => {
  if (!canDetect.value || selectedFiles.value.length === 0) return

  isDetecting.value = true
  errorMessage.value = ''

  try {
    const response = await detectionApi.detectVideo(selectedFiles.value[0])

    if (response.success && response.data) {
      result.value = response.data
    } else {
      errorMessage.value = response.message || '视频检测失败'
    }
  } catch {
    errorMessage.value = '视频检测失败，请检查后端服务是否运行'
  } finally {
    isDetecting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">视频检测</h1>
        <p class="text-slate-400">上传PCB视频进行逐帧缺陷检测</p>
      </div>

      <div class="grid lg:grid-cols-2 gap-8">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-white">上传视频</h2>
            <Video class="w-5 h-5 text-emerald-400" />
          </div>

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

          <div class="flex flex-col sm:flex-row gap-4 mt-6">
            <button
              v-if="canDetect"
              @click="performVideoDetection"
              class="btn-primary flex items-center justify-center space-x-2"
              :disabled="isDetecting"
            >
              <Play v-if="!isDetecting" class="w-5 h-5" />
              <Pause v-else class="w-5 h-5 animate-spin" />
              <span>{{ isDetecting ? '检测中...' : '开始视频检测' }}</span>
            </button>
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
            <p class="text-slate-400">视频检测结果将显示在这里</p>
          </div>

          <div v-else class="space-y-6">
            <div class="grid grid-cols-3 gap-4">
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-emerald-400 mb-1">{{ result.total_frames }}</div>
                <div class="text-sm text-slate-400">总帧数</div>
              </div>
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-green-400 mb-1">{{ result.processed_frames }}</div>
                <div class="text-sm text-slate-400">已处理</div>
              </div>
              <div class="bg-slate-700/50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-yellow-400 mb-1">
                  {{ result.results.reduce((sum, r) => sum + r.total_objects, 0) }}
                </div>
                <div class="text-sm text-slate-400">总缺陷数</div>
              </div>
            </div>

            <div class="bg-slate-700/30 rounded-xl p-4">
              <h3 class="text-white font-medium mb-3">检测统计</h3>
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="(frameResult, index) in result.results"
                  :key="index"
                  class="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                >
                  <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400 font-medium">
                      {{ index + 1 }}
                    </div>
                    <div>
                      <div class="text-white text-sm">第 {{ frameResult.frame_index }} 帧</div>
                      <div class="text-xs text-slate-400">时间: {{ frameResult.timestamp.toFixed(2) }}s</div>
                    </div>
                  </div>
                  <div class="text-white text-sm">
                    {{ frameResult.total_objects }} 个缺陷
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