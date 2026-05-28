import axios from 'axios'
import type {
  DetectionResponse,
  BatchDetectionResponse,
  TargetListResponse,
  ModelListResponse,
  CurrentModelResponse,
  DetectionStatsResponse,
  VideoDetectionResponse
} from '@/types'

// 认证令牌管理
const TOKEN_KEY = 'pcb_token'
const USER_KEY = 'pcb_user'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Accept': 'application/json'
  }
})

// 请求拦截器 - 添加认证令牌
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    // 如果是 401 未认证，清除本地存储
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      // 可以在这里添加跳转到登录页面的逻辑
    }
    return Promise.reject(error)
  }
)

// 认证 API
export const authApi = {
  login: async (username: string, password: string): Promise<any> => {
    const response = await api.post('/auth/login-json', {
      username,
      password
    })
    if (response.data.success && response.data.data?.access_token) {
      localStorage.setItem(TOKEN_KEY, response.data.data.access_token)
    }
    return response.data
  },

  register: async (username: string, email: string, password: string): Promise<any> => {
    const response = await api.post('/auth/register', {
      username,
      email,
      password
    })
    if (response.data.success && response.data.data?.access_token) {
      localStorage.setItem(TOKEN_KEY, response.data.data.access_token)
    }
    return response.data
  },

  logout: async (): Promise<any> => {
    try {
      await api.post('/auth/logout')
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
    return { success: true, message: '登出成功' }
  },

  getCurrentUser: async (): Promise<any> => {
    const response = await api.get('/auth/me')
    if (response.data.success && response.data.data) {
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.data))
    }
    return response.data
  },

  updateUser: async (data: { nickname?: string; avatar_url?: string; password?: string }): Promise<any> => {
    const response = await api.put('/auth/me', data)
    if (response.data.success && response.data.data) {
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.data))
    }
    return response.data
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem(TOKEN_KEY)
  },

  getToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEY)
  },

  getUser: (): any => {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  }
}

// 历史记录 API
export const historyApi = {
  getList: async (page: number = 1, pageSize: number = 20, type?: string): Promise<any> => {
    const params: any = { page, page_size: pageSize }
    if (type) {
      params.type = type
    }
    const response = await api.get('/history/', { params })
    return response.data
  },

  getDetail: async (recordId: string): Promise<any> => {
    const response = await api.get(`/history/${recordId}`)
    return response.data
  },

  delete: async (recordId: string): Promise<any> => {
    const response = await api.delete(`/history/${recordId}`)
    return response.data
  },

  deleteAll: async (): Promise<any> => {
    const response = await api.delete('/history/')
    return response.data
  }
}

// 检测 API
export const detectionApi = {
  detectSingle: async (file: File, modelName?: string): Promise<DetectionResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (modelName) {
      formData.append('model_name', modelName)
    }
    const response = await api.post('/detection/single', formData)
    return response.data
  },

  detectBatch: async (files: File[], modelName?: string): Promise<BatchDetectionResponse> => {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    if (modelName) {
      formData.append('model_name', modelName)
    }
    const response = await api.post('/detection/batch', formData)
    return response.data
  },

  detectRealtime: async (
    imageBase64: string,
    confThreshold: number = 0.5,
    iouThreshold: number = 0.45
  ) => {
    const formData = new FormData()
    formData.append('image_base64', imageBase64)
    formData.append('conf_threshold', confThreshold.toString())
    formData.append('iou_threshold', iouThreshold.toString())
    
    const response = await api.post('/detection/realtime', formData)
    return response.data
  },

  detectVideo: async (file: File, modelName?: string): Promise<VideoDetectionResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (modelName) {
      formData.append('model_name', modelName)
    }
    const response = await api.post('/detection/video', formData)
    return response.data
  },

  getTargets: async (): Promise<TargetListResponse> => {
    const response = await api.get('/detection/targets/list')
    return response.data
  },

  getStats: async (): Promise<DetectionStatsResponse> => {
    const response = await api.get('/detection/stats')
    return response.data
  },

  resetStats: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/detection/stats/reset')
    return response.data
  }
}

export const modelApi = {
  getList: async (): Promise<ModelListResponse> => {
    const response = await api.get('/detection/models/list')
    return response.data
  },

  getCurrent: async (): Promise<CurrentModelResponse> => {
    const response = await api.get('/detection/models/current')
    return response.data
  },

  switchModel: async (modelName: string): Promise<CurrentModelResponse> => {
    const formData = new FormData()
    formData.append('model_name', modelName)
    const response = await api.post('/detection/models/switch', formData)
    return response.data
  }
}

export default api
