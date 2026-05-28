export interface DetectionBox {
  x1: number
  y1: number
  x2: number
  y2: number
  confidence: number
  class_id: number
  class_name: string
  chinese_name: string
  color: string
}

export interface DetectionResult {
  detection_id: string
  image_url: string
  result_image_url: string
  boxes: DetectionBox[]
  total_objects: number
  detection_time: number
  model_name: string
  created_at: string
}

export interface DetectionResponse {
  success: boolean
  message: string
  data: DetectionResult | null
}

export interface BatchDetectionResult {
  total: number
  success: number
  failed: number
  items: Array<{
    filename: string
    success: boolean
    result?: DetectionResult
    error?: string
  }>
}

export interface BatchDetectionResponse {
  success: boolean
  message: string
  data: BatchDetectionResult | null
}

export interface TargetItem {
  id: number
  name: string
  chinese_name: string
  description: string | null
  color: string
}

export interface TargetListResponse {
  success: boolean
  message: string
  data: TargetItem[]
}

export interface ModelItem {
  name: string
  version: string
  status: string
  path: string | null
  description: string | null
  class_names: string[] | null
  created_at: string | null
  last_used: string | null
}

export interface ModelListResponse {
  success: boolean
  message: string
  data: ModelItem[]
}

export interface CurrentModelResponse {
  success: boolean
  message: string
  data: ModelItem | null
}

export interface VideoFrameDetection {
  frame_index: number
  timestamp: number
  boxes: DetectionBox[]
  total_objects: number
  detection_time: number
  model_name: string
}

export interface VideoDetectionResult {
  total_frames: number
  processed_frames: number
  results: VideoFrameDetection[]
}

export interface VideoDetectionResponse {
  success: boolean
  message: string
  data: VideoDetectionResult | null
}

export interface DetectionStatsResponse {
  success: boolean
  message: string
  data: {
    total_detections: number
    total_objects: number
    total_time: number
    avg_detection_time: number
    last_detection_time: string | null
  }
}

// 用户相关类型
export interface User {
  id: string
  username: string
  email: string
  nickname: string | null
  avatar_url: string | null
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AuthResponse {
  success: boolean
  message: string
  data: Token | null
}

export interface UserAuthResponse {
  success: boolean
  message: string
  data: User | null
}

// 历史记录相关类型
export interface DetectionRecordItem {
  id: string
  type: string
  status: string
  model_name: string
  total_objects: number
  detection_time: number | null
  original_image_url: string | null
  result_image_url: string | null
  created_at: string
  boxes: DetectionBox[] | null
}

export interface DetectionHistoryResponse {
  success: boolean
  message: string
  data: DetectionRecordItem[]
  total: number
  page: number
  page_size: number
}

export interface DetectionRecordDetailResponse {
  success: boolean
  message: string
  data: DetectionRecordItem | null
}
