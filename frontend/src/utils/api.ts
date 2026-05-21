import axios from 'axios'
import type {
  SingleDetectionResponse,
  HistoryResponse,
  TargetListResponse,
  ModelListResponse,
  CurrentModelResponse,
  UserRegisterRequest,
  UserLoginRequest,
  UserResponse
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const detectionApi = {
  detectSingle: async (file: File, modelName?: string): Promise<SingleDetectionResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (modelName) {
      formData.append('model_name', modelName)
    }
    const response = await api.post('/detection/single', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  
  getHistory: async (page = 1, pageSize = 10): Promise<HistoryResponse> => {
    const response = await api.get('/detection/history', {
      params: { page, page_size: pageSize }
    })
    return response.data
  },
  
  getDetectionById: async (id: string): Promise<SingleDetectionResponse> => {
    const response = await api.get(`/detection/${id}`)
    return response.data
  },
  
  deleteDetection: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/detection/${id}`)
    return response.data
  },
  
  getTargets: async (): Promise<TargetListResponse> => {
    const response = await api.get('/detection/targets/list')
    return response.data
  }
}

export const modelApi = {
  getList: async (): Promise<ModelListResponse> => {
    const response = await api.get('/model/list')
    return response.data
  },
  
  getCurrent: async (): Promise<CurrentModelResponse> => {
    const response = await api.get('/model/current')
    return response.data
  },
  
  reload: async (objectName?: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/model/reload', objectName ? { object_name: objectName } : {})
    return response.data
  }
}

export const userApi = {
  register: async (data: UserRegisterRequest): Promise<UserResponse> => {
    const response = await api.post('/user/register', data)
    return response.data
  },
  
  login: async (data: UserLoginRequest): Promise<UserResponse> => {
    const response = await api.post('/user/login', data)
    return response.data
  }
}

export default api