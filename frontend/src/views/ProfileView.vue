<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { User, Settings, Lock, Save, LogOut, Mail, User as UserIcon, UploadCloud, Check } from 'lucide-vue-next'
import { authApi } from '@/utils/api'
import type { User as UserType } from '@/types'

const user = ref<UserType | null>(null)
const isSaving = ref(false)
const isChangingPassword = ref(false)
const showSuccess = ref(false)
const errorMessage = ref('')

const userForm = reactive({
  username: '',
  email: '',
  nickname: '',
  avatar_url: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const fetchUser = async () => {
  try {
    const result = await authApi.getCurrentUser()
    if (result.success && result.data) {
      user.value = result.data
      userForm.username = result.data.username
      userForm.email = result.data.email
      userForm.nickname = result.data.nickname || ''
      userForm.avatar_url = result.data.avatar_url || ''
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const saveProfile = async () => {
  if (!user.value) return
  
  errorMessage.value = ''
  isSaving.value = true

  try {
    const data: any = {}
    if (userForm.nickname !== user.value.nickname) {
      data.nickname = userForm.nickname
    }
    if (userForm.avatar_url !== user.value.avatar_url) {
      data.avatar_url = userForm.avatar_url
    }
    
    if (Object.keys(data).length > 0) {
      const result = await authApi.updateUser(data)
      if (result.success && result.data) {
        user.value = result.data
        showSuccess.value = true
        setTimeout(() => showSuccess.value = false, 3000)
      } else {
        errorMessage.value = result.message || '更新失败'
      }
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '更新失败，请稍后重试'
  } finally {
    isSaving.value = false
  }
}

const changePassword = async () => {
  if (!user.value) return
  
  errorMessage.value = ''
  
  if (!passwordForm.currentPassword) {
    errorMessage.value = '请输入当前密码'
    return
  }
  if (!passwordForm.newPassword) {
    errorMessage.value = '请输入新密码'
    return
  }
  if (passwordForm.newPassword.length < 6) {
    errorMessage.value = '新密码长度至少 6 个字符'
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }
  
  isSaving.value = true

  try {
    const result = await authApi.updateUser({ password: passwordForm.newPassword })
    if (result.success) {
      isChangingPassword.value = false
      passwordForm.currentPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
      showSuccess.value = true
      setTimeout(() => showSuccess.value = false, 3000)
    } else {
      errorMessage.value = result.message || '修改密码失败'
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '修改密码失败，请稍后重试'
  } finally {
    isSaving.value = false
  }
}

const handleLogout = () => {
  authApi.logout()
  window.location.reload()
}

onMounted(() => {
  fetchUser()
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 pt-20">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 页面头部 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <User class="w-8 h-8 text-emerald-400" />
          个人中心
        </h1>
        <p class="text-slate-400">管理您的账户信息</p>
      </div>

      <!-- 成功提示 -->
      <div
        v-if="showSuccess"
        class="mb-6 bg-green-900/30 border border-green-500/50 text-green-400 px-4 py-3 rounded-xl flex items-center gap-3"
      >
        <Check class="w-5 h-5" />
        <span>保存成功！</span>
      </div>

      <!-- 错误提示 -->
      <div
        v-if="errorMessage"
        class="mb-6 bg-red-900/30 border border-red-500/50 text-red-400 px-4 py-3 rounded-xl"
      >
        {{ errorMessage }}
      </div>

      <!-- 用户卡片 -->
      <div class="bg-slate-800/50 rounded-2xl border border-slate-700 overflow-hidden">
        <!-- 用户信息 -->
        <div class="p-8 border-b border-slate-700">
          <div class="flex items-start gap-6">
            <!-- 头像 -->
            <div class="flex-shrink-0">
              <div class="relative">
                <div class="w-24 h-24 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center text-white text-3xl font-bold">
                  {{ user?.username.charAt(0).toUpperCase() }}
                </div>
                <button
                  class="absolute -bottom-1 -right-1 w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-600"
                  title="上传头像"
                >
                  <UploadCloud class="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <!-- 基本信息 -->
            <div class="flex-1">
              <h2 class="text-2xl font-bold text-white mb-1">
                {{ user?.nickname || user?.username }}
              </h2>
              <p class="text-slate-400">@{{ user?.username }}</p>
              <p class="text-slate-500 text-sm mt-1 flex items-center gap-2">
                <Mail class="w-4 h-4" />
                {{ user?.email }}
              </p>
            </div>
            
            <!-- 角色标识 -->
            <div class="flex-shrink-0">
              <span class="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-medium">
                {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 设置表单 -->
        <div class="p-8">
          <h3 class="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Settings class="w-5 h-5 text-emerald-400" />
            账户设置
          </h3>

          <div class="space-y-6">
            <!-- 昵称 -->
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">昵称</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center text-slate-500">
                  <UserIcon class="w-5 h-5" />
                </div>
                <input
                  v-model="userForm.nickname"
                  type="text"
                  placeholder="请输入昵称"
                  class="w-full pl-12 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <!-- 邮箱 -->
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">邮箱</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center text-slate-500">
                  <Mail class="w-5 h-5" />
                </div>
                <input
                  v-model="userForm.email"
                  type="email"
                  placeholder="请输入邮箱"
                  disabled
                  class="w-full pl-12 pr-4 py-3 bg-slate-900/30 border border-slate-700 rounded-xl text-slate-500 cursor-not-allowed"
                />
              </div>
              <p class="mt-2 text-xs text-slate-500">邮箱绑定后不可修改</p>
            </div>

            <!-- 用户名 -->
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">用户名</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center text-slate-500">
                  <User class="w-5 h-5" />
                </div>
                <input
                  v-model="userForm.username"
                  type="text"
                  placeholder="请输入用户名"
                  disabled
                  class="w-full pl-12 pr-4 py-3 bg-slate-900/30 border border-slate-700 rounded-xl text-slate-500 cursor-not-allowed"
                />
              </div>
              <p class="mt-2 text-xs text-slate-500">用户名注册后不可修改</p>
            </div>

            <!-- 保存按钮 -->
            <button
              @click="saveProfile"
              :disabled="isSaving"
              class="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-600 text-white font-medium rounded-xl hover:from-emerald-600 hover:to-green-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save class="w-5 h-5" />
              {{ isSaving ? '保存中...' : '保存更改' }}
            </button>
          </div>

          <!-- 修改密码 -->
          <div class="mt-12 pt-8 border-t border-slate-700">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-semibold text-white flex items-center gap-2">
                <Lock class="w-5 h-5 text-emerald-400" />
                修改密码
              </h3>
              <button
                @click="isChangingPassword = !isChangingPassword"
                class="text-sm text-emerald-400 hover:text-emerald-300"
              >
                {{ isChangingPassword ? '收起' : '展开' }}
              </button>
            </div>

            <div v-if="isChangingPassword" class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">当前密码</label>
                <input
                  v-model="passwordForm.currentPassword"
                  type="password"
                  placeholder="请输入当前密码"
                  class="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">新密码</label>
                <input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="请输入新密码（至少6位）"
                  class="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">确认新密码</label>
                <input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  class="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                />
              </div>

              <button
                @click="changePassword"
                :disabled="isSaving"
                class="px-6 py-3 bg-slate-700 text-white font-medium rounded-xl hover:bg-slate-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Lock class="w-5 h-5" />
                {{ isSaving ? '修改中...' : '修改密码' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 退出登录 -->
      <div class="mt-8">
        <button
          @click="handleLogout"
          class="w-full sm:w-auto px-6 py-3 bg-red-500/10 border border-red-500/20 text-red-400 font-medium rounded-xl hover:bg-red-500/20 transition-all flex items-center justify-center gap-2"
        >
          <LogOut class="w-5 h-5" />
          退出登录
        </button>
      </div>

      <!-- 账户信息 -->
      <div class="mt-8 text-sm text-slate-500">
        <p>账户创建于: {{ user?.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-' }}</p>
        <p class="mt-1">最后更新: {{ user?.updated_at ? new Date(user.updated_at).toLocaleString('zh-CN') : '-' }}</p>
      </div>
    </div>
  </div>
</template>
