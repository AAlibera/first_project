import axios from 'axios'
import type {
  DetectionResponse,
  BatchDetectionResponse,
  TargetListResponse,
  ModelListResponse,
  CurrentModelResponse,
  DetectionStatsResponse
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const detectionApi = {
  detectSingle: async (file: File, modelName?: string): Promise<DetectionResponse> => {
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

  detectBatch: async (files: File[], modelName?: string): Promise<BatchDetectionResponse> => {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`file_${index}`, file)
    })
    if (modelName) {
      formData.append('model_name', modelName)
    }
    const response = await api.post('/detection/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
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

  switch: async (modelName: string): Promise<CurrentModelResponse> => {
    const response = await api.post('/detection/models/switch', { model_name: modelName })
    return response.data
  }
}

export default api
