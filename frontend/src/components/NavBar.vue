<script setup lang="ts">
import { ref, computed } from 'vue'
import { Image, Folder, Video, Camera, Home, Menu, X, User, LogOut, Clock, Settings } from 'lucide-vue-next'

interface NavItem {
  name: string
  icon: typeof Home
  path: string
}

const isMenuOpen = ref(false)
const isUserMenuOpen = ref(false)

const username = computed(() => {
  return localStorage.getItem('username') || '用户'
})

const navItems: NavItem[] = [
  { name: '首页', icon: Home, path: '/' },
  { name: '单图检测', icon: Image, path: '/single' },
  { name: '文件夹', icon: Folder, path: '/folder' },
  { name: '视频检测', icon: Video, path: '/video' },
  { name: '摄像头', icon: Camera, path: '/camera' },
  { name: '历史记录', icon: Clock, path: '/history' }
]

const emit = defineEmits<{
  navigate: [path: string]
  logout: []
}>()

const handleNavigate = (path: string) => {
  emit('navigate', path)
  isMenuOpen.value = false
}

const handleLogout = () => {
  emit('logout')
  isUserMenuOpen.value = false
}
</script>

<template>
  <nav class="fixed top-0 left-0 right-0 z-50 glass">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center space-x-3 cursor-pointer" @click="handleNavigate('/')">
          <div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center">
            <Camera class="w-6 h-6 text-white" />
          </div>
          <span class="text-xl font-bold text-white">PCB 缺陷检测系统</span>
        </div>

        <div class="hidden md:flex items-center space-x-1">
          <button
            v-for="item in navItems"
            :key="item.path"
            @click="handleNavigate(item.path)"
            class="flex items-center space-x-2 px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <span>{{ item.name }}</span>
          </button>

          <div class="relative ml-4">
            <button
              @click="isUserMenuOpen = !isUserMenuOpen"
              class="flex items-center space-x-2 px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
            >
              <User class="w-5 h-5" />
              <span>{{ username }}</span>
            </button>

            <div
              v-if="isUserMenuOpen"
              class="absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-xl border border-slate-700 py-2"
            >
              <button
                @click="handleNavigate('/profile')"
                class="flex items-center space-x-2 w-full px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-700 transition-all"
              >
                <Settings class="w-4 h-4" />
                <span>个人中心</span>
              </button>
              <div class="border-t border-slate-700 my-1"></div>
              <button
                @click="handleLogout"
                class="flex items-center space-x-2 w-full px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-700 transition-all"
              >
                <LogOut class="w-4 h-4" />
                <span>退出登录</span>
              </button>
            </div>
          </div>
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
          @click="handleNavigate(item.path)"
          class="flex items-center space-x-3 w-full px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
        >
          <component :is="item.icon" class="w-5 h-5" />
          <span>{{ item.name }}</span>
        </button>

        <div class="border-t border-slate-700 my-2 pt-2">
          <div class="px-4 py-2 text-slate-400 text-sm">
            欢迎, {{ username }}
          </div>
          <button
            @click="handleNavigate('/profile')"
            class="flex items-center space-x-3 w-full px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
          >
            <Settings class="w-5 h-5" />
            <span>个人中心</span>
          </button>
          <button
            @click="handleLogout"
            class="flex items-center space-x-3 w-full px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
          >
            <LogOut class="w-5 h-5" />
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>