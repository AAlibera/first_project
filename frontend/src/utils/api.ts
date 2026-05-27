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

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Accept': 'application/json'
  }
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
