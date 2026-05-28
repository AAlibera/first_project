<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Upload, User, Lock, Mail, Check } from 'lucide-vue-next'
import { authApi } from '@/utils/api'

const emit = defineEmits<{
  (e: 'register-success'): void
  (e: 'switch-to-login'): void
}>()

const isLoading = ref(false)
const errorMessage = ref('')

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agree: false
})

const validateForm = () => {
  if (!registerForm.username.trim()) {
    errorMessage.value = '请输入用户名'
    return false
  }
  if (registerForm.username.length < 3 || registerForm.username.length > 50) {
    errorMessage.value = '用户名长度必须在 3 到 50 个字符之间'
    return false
  }
  if (!registerForm.email.trim()) {
    errorMessage.value = '请输入邮箱'
    return false
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
    errorMessage.value = '请输入有效的邮箱地址'
    return false
  }
  if (!registerForm.password) {
    errorMessage.value = '请输入密码'
    return false
  }
  if (registerForm.password.length < 6) {
    errorMessage.value = '密码长度至少 6 个字符'
    return false
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return false
  }
  if (!registerForm.agree) {
    errorMessage.value = '请同意服务条款'
    return false
  }
  return true
}

const handleRegister = async () => {
  errorMessage.value = ''
  
  if (!validateForm()) {
    return
  }
  
  isLoading.value = true

  try {
    const result = await authApi.register(
      registerForm.username,
      registerForm.email,
      registerForm.password
    )
    
    if (result.success) {
      emit('register-success')
    } else {
      errorMessage.value = result.message || '注册失败'
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '注册失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <div class="logo-icon">
          <Upload class="w-8 h-8 text-white" />
        </div>
        <h1 class="register-title">创建账号</h1>
        <p class="register-subtitle">加入我们，开始智能检测之旅</p>
      </div>

      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label class="form-label">
            <User class="w-4 h-4" />
            <span>用户名</span>
          </label>
          <input
            v-model="registerForm.username"
            type="text"
            class="form-input"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label class="form-label">
            <Mail class="w-4 h-4" />
            <span>邮箱</span>
          </label>
          <input
            v-model="registerForm.email"
            type="email"
            class="form-input"
            placeholder="请输入邮箱"
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label">
            <Lock class="w-4 h-4" />
            <span>密码</span>
          </label>
          <input
            v-model="registerForm.password"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            autocomplete="new-password"
          />
        </div>

        <div class="form-group">
          <label class="form-label">
            <Lock class="w-4 h-4" />
            <span>确认密码</span>
          </label>
          <input
            v-model="registerForm.confirmPassword"
            type="password"
            class="form-input"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <div class="form-actions">
          <label class="checkbox-label">
            <input
              v-model="registerForm.agree"
              type="checkbox"
              class="checkbox-input"
            />
            <span class="checkbox-custom"></span>
            <span>我已阅读并同意</span>
            <a href="#" class="terms-link">《服务条款》</a>
            <span>和</span>
            <a href="#" class="terms-link">《隐私政策》</a>
          </label>
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button
          type="submit"
          class="register-btn"
          :disabled="isLoading"
        >
          <Check v-if="!isLoading" class="w-5 h-5" />
          <div v-else class="loading-spinner"></div>
          <span>{{ isLoading ? '注册中...' : '注册' }}</span>
        </button>
      </form>

      <div class="login-link">
        <span>已有账号？</span>
        <a href="#" @click.prevent="$emit('switch-to-login')">立即登录</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

.register-title {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.register-subtitle {
  font-size: 14px;
  color: #6b7280;
  letter-spacing: 2px;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-label svg {
  color: #10b981;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  font-size: 15px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
  color: #1f2937;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #10b981;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
}

.form-input::placeholder {
  color: #9ca3af;
}

.form-actions {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-top: 4px;
  flex-wrap: wrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  user-select: none;
  flex-wrap: wrap;
}

.terms-link {
  color: #10b981;
  text-decoration: none;
  font-weight: 500;
}

.terms-link:hover {
  text-decoration: underline;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 18px;
  height: 18px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  position: relative;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.checkbox-input:checked + .checkbox-custom {
  background: #10b981;
  border-color: #10b981;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.error-message {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}

.register-btn {
  width: 100%;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

.register-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.register-btn:active:not(:disabled) {
  transform: translateY(0);
}

.register-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-link {
  margin-top: 32px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.login-link a {
  color: #10b981;
  text-decoration: none;
  font-weight: 600;
  margin-left: 6px;
  transition: color 0.2s;
}

.login-link a:hover {
  color: #059669;
  text-decoration: underline;
}
</style>
