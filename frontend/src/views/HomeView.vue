<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Zap, Shield, TrendingUp, Camera, ArrowRight } from 'lucide-vue-next'
import TargetBadge from '@/components/TargetBadge.vue'
import { detectionApi } from '@/utils/api'
import type { TargetItem } from '@/types'

const targets = ref<TargetItem[]>([])
const isLoading = ref(true)

const features = [
  {
    icon: Zap,
    title: '实时检测',
    description: '毫秒级响应，实时检测PCB板缺陷，支持多种检测模式'
  },
  {
    icon: Shield,
    title: '高精度识别',
    description: '基于先进的深度学习模型，精准识别各类PCB表面缺陷'
  },
  {
    icon: TrendingUp,
    title: '批量处理',
    description: '支持文件夹批量检测、视频流检测，提升生产效率'
  }
]

onMounted(async () => {
  try {
    const response = await detectionApi.getTargets()
    if (response.success) {
      targets.value = response.data
    }
  } catch {
    targets.value = [
      { id: 0, name: 'scratch', chinese_name: '划痕', description: 'PCB板表面划痕', color: '#f87171' },
      { id: 1, name: 'crack', chinese_name: '裂纹', description: 'PCB板表面裂纹', color: '#fb923c' },
      { id: 2, name: 'hole', chinese_name: '孔洞', description: 'PCB板表面孔洞缺陷', color: '#facc15' },
      { id: 3, name: 'deformation', chinese_name: '变形', description: 'PCB板变形缺陷', color: '#34d399' },
      { id: 4, name: 'missing', chinese_name: '缺失', description: '元器件缺失', color: '#38bdf8' },
      { id: 5, name: 'solder', chinese_name: '焊点异常', description: '焊接点质量问题', color: '#a78bfa' }
    ]
  } finally {
    isLoading.value = false
  }
})

defineEmits<{
  navigate: [path: string]
}>()
</script>

<template>
  <div class="min-h-screen pt-16">
    <section class="relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-emerald-900/30 via-transparent to-green-900/30"></div>
      <div class="absolute top-20 left-10 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute bottom-20 right-10 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-pulse-slow" style="animation-delay: 1s;"></div>

      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div class="text-center max-w-3xl mx-auto">
          <div class="inline-flex items-center space-x-2 px-4 py-2 bg-emerald-500/20 rounded-full text-emerald-400 text-sm mb-8 animate-fade-in">
            <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
            <span>PCB 缺陷智能检测平台</span>
          </div>

          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 animate-slide-up">
            PCB
            <span class="bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">缺陷检测</span>
            系统
          </h1>

          <p class="text-lg text-slate-400 mb-10 animate-slide-up" style="animation-delay: 0.1s;">
            基于深度学习技术，快速准确检测PCB板各类缺陷，保障产品质量，提升生产效率
          </p>

          <div class="flex flex-col sm:flex-row gap-4 justify-center items-center animate-slide-up" style="animation-delay: 0.2s;">
            <button
              @click="$emit('navigate', '/single')"
              class="btn-primary flex items-center space-x-2"
            >
              <Camera class="w-5 h-5" />
              <span>开始检测</span>
              <ArrowRight class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-white mb-4">平台功能</h2>
          <p class="text-slate-400">多种检测模式，满足不同场景需求</p>
        </div>

        <div class="grid md:grid-cols-3 gap-6">
          <div
            v-for="(feature, index) in features"
            :key="index"
            class="card p-6 hover:border-emerald-500/50 transition-all duration-300 group"
          >
            <div class="w-14 h-14 bg-gradient-to-br from-emerald-500/20 to-green-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <component :is="feature.icon" class="w-7 h-7 text-emerald-400" />
            </div>
            <h3 class="text-xl font-semibold text-white mb-2">{{ feature.title }}</h3>
            <p class="text-slate-400">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 bg-slate-800/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-white mb-4">检测缺陷类型</h2>
          <p class="text-slate-400">系统支持多种PCB表面缺陷的智能识别</p>
        </div>

        <div v-if="!isLoading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <TargetBadge
            v-for="target in targets"
            :key="target.id"
            :target="target"
          />
        </div>

        <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="i in 6"
            :key="i"
            class="h-24 bg-slate-700/30 rounded-xl animate-pulse"
          ></div>
        </div>
      </div>
    </section>

    <section class="py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-white mb-4">选择检测方式</h2>
          <p class="text-slate-400">根据您的需求选择合适的检测模式</p>
        </div>

        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button
            @click="$emit('navigate', '/single')"
            class="card p-6 text-left hover:border-emerald-500/50 transition-all duration-300 group"
          >
            <div class="w-16 h-16 bg-gradient-to-br from-emerald-500/30 to-green-500/30 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Image class="w-8 h-8 text-emerald-400" />
            </div>
            <h3 class="text-lg font-semibold text-white mb-2">单图检测</h3>
            <p class="text-slate-400 text-sm">上传单张PCB图片进行快速检测</p>
          </button>

          <button
            @click="$emit('navigate', '/folder')"
            class="card p-6 text-left hover:border-emerald-500/50 transition-all duration-300 group"
          >
            <div class="w-16 h-16 bg-gradient-to-br from-emerald-500/30 to-green-500/30 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Folder class="w-8 h-8 text-emerald-400" />
            </div>
            <h3 class="text-lg font-semibold text-white mb-2">文件夹检测</h3>
            <p class="text-slate-400 text-sm">批量上传多个图片文件进行检测</p>
          </button>

          <button
            @click="$emit('navigate', '/video')"
            class="card p-6 text-left hover:border-emerald-500/50 transition-all duration-300 group"
          >
            <div class="w-16 h-16 bg-gradient-to-br from-emerald-500/30 to-green-500/30 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Video class="w-8 h-8 text-emerald-400" />
            </div>
            <h3 class="text-lg font-semibold text-white mb-2">视频检测</h3>
            <p class="text-slate-400 text-sm">上传视频文件进行逐帧缺陷检测</p>
          </button>

          <button
            @click="$emit('navigate', '/camera')"
            class="card p-6 text-left hover:border-emerald-500/50 transition-all duration-300 group"
          >
            <div class="w-16 h-16 bg-gradient-to-br from-emerald-500/30 to-green-500/30 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Camera class="w-8 h-8 text-emerald-400" />
            </div>
            <h3 class="text-lg font-semibold text-white mb-2">摄像头检测</h3>
            <p class="text-slate-400 text-sm">使用摄像头进行实时缺陷检测</p>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script lang="ts">
import { Image, Folder, Video } from 'lucide-vue-next'
</script>