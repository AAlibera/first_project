<script setup lang="ts">
import { ref } from 'vue'
import { Image, Folder, Video, Camera, Home, Menu, X } from 'lucide-vue-next'

interface NavItem {
  name: string
  icon: typeof Home
  path: string
}

const isMenuOpen = ref(false)

const navItems: NavItem[] = [
  { name: '首页', icon: Home, path: '/' },
  { name: '单图检测', icon: Image, path: '/single' },
  { name: '文件夹', icon: Folder, path: '/folder' },
  { name: '视频检测', icon: Video, path: '/video' },
  { name: '摄像头', icon: Camera, path: '/camera' }
]

defineEmits<{
  navigate: [path: string]
}>()
</script>

<template>
  <nav class="fixed top-0 left-0 right-0 z-50 glass">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center space-x-3 cursor-pointer" @click="$emit('navigate', '/')">
          <div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center">
            <Camera class="w-6 h-6 text-white" />
          </div>
          <span class="text-xl font-bold text-white">PCB 缺陷检测系统</span>
        </div>

        <div class="hidden md:flex items-center space-x-1">
          <button
            v-for="item in navItems"
            :key="item.path"
            @click="$emit('navigate', item.path)"
            class="flex items-center space-x-2 px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <span>{{ item.name }}</span>
          </button>
        </div>

        <button
          class="md:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10"
          @click="isMenuOpen = !isMenuOpen"
        >
          <Menu v-if="!isMenuOpen" class="w-6 h-6" />
          <X v-else class="w-6 h-6" />
        </button>
      </div>
    </div>

    <div
      v-if="isMenuOpen"
      class="md:hidden glass border-t border-white/10"
    >
      <div class="px-4 py-3 space-y-1">
        <button
          v-for="item in navItems"
          :key="item.path"
          @click="$emit('navigate', item.path); isMenuOpen = false"
          class="flex items-center space-x-3 w-full px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
        >
          <component :is="item.icon" class="w-5 h-5" />
          <span>{{ item.name }}</span>
        </button>
      </div>
    </div>
  </nav>
</template>