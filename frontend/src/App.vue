<script setup lang="ts">
import { ref, onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import HomeView from '@/views/HomeView.vue'
import SingleDetectionView from '@/views/SingleDetectionView.vue'
import FolderDetectionView from '@/views/FolderDetectionView.vue'
import VideoDetectionView from '@/views/VideoDetectionView.vue'
import CameraDetectionView from '@/views/CameraDetectionView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import HistoryView from '@/views/HistoryView.vue'
import ProfileView from '@/views/ProfileView.vue'
import { authApi } from '@/utils/api'

const currentPath = ref('/')
const isAuthenticated = ref(false)
const showLogin = ref(true)
const isCheckingAuth = ref(true)

const handleNavigate = (path: string) => {
  currentPath.value = path
}

const handleLoginSuccess = () => {
  isAuthenticated.value = true
  showLogin.value = true
  currentPath.value = '/'
}

const handleRegisterSuccess = () => {
  isAuthenticated.value = true
  showLogin.value = true
  currentPath.value = '/'
}

const handleSwitchToRegister = () => {
  showLogin.value = false
}

const handleSwitchToLogin = () => {
  showLogin.value = true
}

const handleLogout = () => {
  authApi.logout()
  isAuthenticated.value = false
  showLogin.value = true
  currentPath.value = '/'
}

const verifyUserAuth = async () => {
  if (authApi.isAuthenticated()) {
    try {
      const result = await authApi.getCurrentUser()
      if (result.success && result.data) {
        isAuthenticated.value = true
      } else {
        authApi.logout()
        isAuthenticated.value = false
      }
    } catch (error) {
      console.error('用户验证失败:', error)
      authApi.logout()
      isAuthenticated.value = false
    }
  } else {
    isAuthenticated.value = false
  }
  isCheckingAuth.value = false
}

onMounted(() => {
  verifyUserAuth()
})
</script>

<template>
  <div class="min-h-screen">
    <!-- 认证状态检查中 -->
    <div v-if="isCheckingAuth" class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
      <div class="text-center">
        <div class="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-white text-lg">正在加载...</p>
      </div>
    </div>

    <!-- 未登录状态 -->
    <template v-else-if="!isAuthenticated">
      <LoginView
        v-if="showLogin"
        @login-success="handleLoginSuccess"
        @switch-to-register="handleSwitchToRegister"
      />
      <RegisterView
        v-else
        @register-success="handleRegisterSuccess"
        @switch-to-login="handleSwitchToLogin"
      />
    </template>
    
    <!-- 已登录状态 -->
    <template v-else>
      <NavBar @navigate="handleNavigate" @logout="handleLogout" />

      <HomeView
        v-if="currentPath === '/'"
        @navigate="handleNavigate"
      />
      <SingleDetectionView
        v-else-if="currentPath === '/single'"
      />
      <FolderDetectionView
        v-else-if="currentPath === '/folder'"
      />
      <VideoDetectionView
        v-else-if="currentPath === '/video'"
      />
      <CameraDetectionView
        v-else-if="currentPath === '/camera'"
      />
      <HistoryView
        v-else-if="currentPath === '/history'"
      />
      <ProfileView
        v-else-if="currentPath === '/profile'"
      />

      <footer class="bg-slate-800/50 border-t border-slate-700/50 py-8 mt-auto">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p class="text-slate-400 text-sm">
            © 2024 PCB缺陷检测系统. All rights reserved.
          </p>
        </div>
      </footer>
    </template>
  </div>
</template>