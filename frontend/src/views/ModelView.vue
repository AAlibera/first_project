<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Cog, RefreshCw, Check, Clock, Package, Server } from 'lucide-vue-next'
import { modelApi } from '@/utils/api'
import type { ModelItem } from '@/types'

const currentModel = ref<ModelItem | null>(null)
const modelList = ref<ModelItem[]>([])
const isLoading = ref(true)
const isReloading = ref(false)
const reloadMessage = ref('')

const loadModels = async () => {
  isLoading.value = true
  try {
    const [currentRes, listRes] = await Promise.all([
      modelApi.getCurrent(),
      modelApi.getList()
    ])
    
    if (currentRes.success) {
      currentModel.value = currentRes.data
    }
    if (listRes.success) {
      modelList.value = listRes.data
    }
  } catch {
    currentModel.value = {
      object_name: 'yolo11n.pt',
      metadata: {
        name: 'YOLO11n',
        version: '1.0.0',
        created_at: new Date().toISOString(),
        description: '默认目标检测模型',
        metrics: null,
        config: null
      },
      public_url: ''
    }
    modelList.value = []
  } finally {
    isLoading.value = false
  }
}

const handleReload = async () => {
  isReloading.value = true
  reloadMessage.value = ''
  
  try {
    const response = await modelApi.reload()
    if (response.success) {
      reloadMessage.value = '模型重新加载成功'
      await loadModels()
    } else {
      reloadMessage.value = '模型重新加载失败'
    }
  } catch {
    reloadMessage.value = '模型重新加载失败，请检查后端服务'
  } finally {
    isReloading.value = false
    setTimeout(() => {
      reloadMessage.value = ''
    }, 3000)
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(loadModels)
</script>

<template>
  <div class="min-h-screen pt-16 pb-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center mb-12">
        <h1 class="text-3xl font-bold text-white mb-4">模型管理</h1>
        <p class="text-slate-400">管理和配置目标检测模型</p>
      </div>
      
      <div v-if="isLoading" class="text-center py-16">
        <div class="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-slate-400">加载中...</p>
      </div>
      
      <div v-else class="space-y-8">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-xl flex items-center justify-center">
                <Server class="w-6 h-6 text-primary-400" />
              </div>
              <div>
                <h2 class="text-xl font-semibold text-white">当前使用模型</h2>
                <p class="text-sm text-slate-400">当前服务正在使用的检测模型</p>
              </div>
            </div>
            <button
              @click="handleReload"
              :disabled="isReloading"
              class="btn-primary flex items-center space-x-2 disabled:opacity-50"
            >
              <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isReloading }" />
              <span>{{ isReloading ? '加载中...' : '重新加载' }}</span>
            </button>
          </div>
          
          <div v-if="reloadMessage" class="mb-6 p-4 rounded-lg" :class="reloadMessage.includes('成功') ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'">
            {{ reloadMessage }}
          </div>
          
          <div v-if="currentModel" class="grid md:grid-cols-3 gap-4">
            <div class="bg-slate-700/50 rounded-xl p-4">
              <div class="flex items-center space-x-2 mb-2">
                <Package class="w-5 h-5 text-primary-400" />
                <span class="text-slate-400 text-sm">模型名称</span>
              </div>
              <div class="text-white font-medium">{{ currentModel.metadata?.name || currentModel.object_name }}</div>
            </div>
            
            <div class="bg-slate-700/50 rounded-xl p-4">
              <div class="flex items-center space-x-2 mb-2">
                <Cog class="w-5 h-5 text-accent-400" />
                <span class="text-slate-400 text-sm">版本号</span>
              </div>
              <div class="text-white font-medium">{{ currentModel.metadata?.version || '未知' }}</div>
            </div>
            
            <div class="bg-slate-700/50 rounded-xl p-4">
              <div class="flex items-center space-x-2 mb-2">
                <Clock class="w-5 h-5 text-green-400" />
                <span class="text-slate-400 text-sm">加载时间</span>
              </div>
              <div class="text-white font-medium">{{ currentModel.metadata?.created_at ? formatDate(currentModel.metadata.created_at) : '-' }}</div>
            </div>
          </div>
          
          <div v-if="currentModel?.metadata?.description" class="mt-4 bg-slate-700/30 rounded-xl p-4">
            <div class="text-sm text-slate-400 mb-1">模型描述</div>
            <div class="text-white">{{ currentModel.metadata.description }}</div>
          </div>
          
          <div class="mt-4 flex items-center space-x-2 text-green-400">
            <Check class="w-5 h-5" />
            <span>模型已加载并运行</span>
          </div>
        </div>
        
        <div class="card p-6">
          <h2 class="text-xl font-semibold text-white mb-6">可用模型列表</h2>
          
          <div v-if="modelList.length === 0" class="text-center py-12">
            <div class="w-16 h-16 mx-auto mb-4 bg-slate-700/50 rounded-xl flex items-center justify-center">
              <Package class="w-8 h-8 text-slate-500" />
            </div>
            <p class="text-slate-400">暂无可用模型</p>
          </div>
          
          <div v-else class="space-y-4">
            <div
              v-for="model in modelList"
              :key="model.object_name"
              class="bg-slate-700/30 rounded-xl p-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors cursor-pointer"
            >
              <div>
                <div class="text-white font-medium">{{ model.metadata?.name || model.object_name }}</div>
                <div class="text-sm text-slate-400">版本: {{ model.metadata?.version || '未知' }}</div>
              </div>
              <div class="flex items-center space-x-2">
                <span
                  v-if="model.object_name === currentModel?.object_name"
                  class="px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded-full"
                >
                  当前使用
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="card p-6 bg-gradient-to-r from-primary-900/30 to-accent-900/30">
          <h3 class="text-lg font-semibold text-white mb-4">模型配置说明</h3>
          <ul class="space-y-3 text-slate-400">
            <li class="flex items-start space-x-3">
              <span class="w-6 h-6 bg-primary-500/20 rounded-full flex items-center justify-center text-primary-400 text-sm flex-shrink-0 mt-0.5">1</span>
              <span>模型文件存储在 MinIO 对象存储中，支持自动版本管理</span>
            </li>
            <li class="flex items-start space-x-3">
              <span class="w-6 h-6 bg-primary-500/20 rounded-full flex items-center justify-center text-primary-400 text-sm flex-shrink-0 mt-0.5">2</span>
              <span>系统启动时会自动检测并加载最新版本的模型</span>
            </li>
            <li class="flex items-start space-x-3">
              <span class="w-6 h-6 bg-primary-500/20 rounded-full flex items-center justify-center text-primary-400 text-sm flex-shrink-0 mt-0.5">3</span>
              <span>点击"重新加载"按钮可手动刷新模型配置</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
