<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ImageSearch, Target, Zap, Shield, ArrowRight } from 'lucide-vue-next'
import TargetBadge from '@/components/TargetBadge.vue'
import { detectionApi } from '@/utils/api'
import type { TargetItem } from '@/types'

const targets = ref<TargetItem[]>([])
const isLoading = ref(true)

const features = [
  {
    icon: Zap,
    title: '实时检测',
    description: '基于 YOLO11 模型，毫秒级响应，实时检测遥感图像中的目标'
  },
  {
    icon: Target,
    title: '多目标识别',
    description: '支持飞机、油罐、立交桥、操场四种遥感目标的精准识别'
  },
  {
    icon: Shield,
    title: '数据安全',
    description: '采用 MinIO 对象存储，确保您的数据安全可靠'
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
      { id: 0, name: 'aircraft', chinese_name: '飞机', description: '固定翼飞机、直升机等' },
      { id: 1, name: 'oiltank', chinese_name: '油罐', description: '储油罐、化工罐等' },
      { id: 2, name: 'overpass', chinese_name: '立交桥', description: '各类立交桥' },
      { id: 3, name: 'playground', chinese_name: '操场', description: '运动场、操场等' }
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
      <div class="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-900/20"></div>
      <div class="absolute top-20 left-10 w-72 h-72 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute bottom-20 right-10 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl animate-pulse-slow" style="animation-delay: 1s;"></div>
      
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div class="text-center max-w-3xl mx-auto">
          <div class="inline-flex items-center space-x-2 px-4 py-2 bg-primary-500/20 rounded-full text-primary-400 text-sm mb-8 animate-fade-in">
            <span class="w-2 h-2 bg-primary-400 rounded-full animate-pulse"></span>
            <span>遥感图像目标检测平台</span>
          </div>
          
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 animate-slide-up">
            智能遥感图像
            <span class="bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">目标检测</span>
          </h1>
          
          <p class="text-lg text-slate-400 mb-10 animate-slide-up" style="animation-delay: 0.1s;">
            基于深度学习技术，快速准确地检测遥感图像中的飞机、油罐、立交桥等目标，助力遥感数据分析与决策支持
          </p>
          
          <div class="flex flex-col sm:flex-row gap-4 justify-center items-center animate-slide-up" style="animation-delay: 0.2s;">
            <button
              @click="$emit('navigate', '/detection')"
              class="btn-primary flex items-center space-x-2"
            >
              <ImageSearch class="w-5 h-5" />
              <span>开始检测</span>
              <ArrowRight class="w-5 h-5" />
            </button>
            <button
              @click="$emit('navigate', '/history')"
              class="btn-secondary"
            >
              查看历史记录
            </button>
          </div>
        </div>
      </div>
    </section>
    
    <section class="py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-white mb-4">平台特性</h2>
          <p class="text-slate-400">高性能、高精度、高可靠性的遥感目标检测解决方案</p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-6">
          <div
            v-for="(feature, index) in features"
            :key="index"
            class="card p-6 hover:border-primary-500/50 transition-all duration-300 group"
          >
            <div class="w-14 h-14 bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <component :is="feature.icon" class="w-7 h-7 text-primary-400" />
            </div>
            <h3 class="text-xl font-semibold text-white mb-2">{{ feature.title }}</h3>
            <p class="text-slate-400">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>
    
    <section class="py-20 bg-slate-800/30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-white mb-4">支持的检测目标</h2>
          <p class="text-slate-400">覆盖多种遥感场景下的常见目标类型</p>
        </div>
        
        <div v-if="!isLoading" class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <TargetBadge
            v-for="target in targets"
            :key="target.id"
            :target="target"
          />
        </div>
        
        <div v-else class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="i in 4"
            :key="i"
            class="h-24 bg-slate-700/30 rounded-xl animate-pulse"
          ></div>
        </div>
      </div>
    </section>
    
    <section class="py-20">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="card p-8 md:p-12">
          <div class="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl flex items-center justify-center">
            <ImageSearch class="w-10 h-10 text-white" />
          </div>
          <h3 class="text-2xl font-bold text-white mb-4">准备好开始了吗？</h3>
          <p class="text-slate-400 mb-8">上传您的遥感图像，体验先进的目标检测技术</p>
          <button
            @click="$emit('navigate', '/detection')"
            class="btn-primary text-lg px-8 py-3"
          >
            立即开始检测
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
