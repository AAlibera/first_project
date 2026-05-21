export interface DetectionBox {
  x1: number
  y1: number
  x2: number
  y2: number
  confidence: number
  class_id: number
  class_name: string
  chinese_name: string | null
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

export interface SingleDetectionResponse {
  success: boolean
  message: string
  data: DetectionResult | null
}

export interface HistoryItem {
  id: string
  image_url: string
  result_image_url: string
  total_objects: number
  created_at: string
  model_name: string
  filename: string
  status: string
  type: string
  time: string
  count: number
  detected_targets: string[]
}

export interface HistoryResponse {
  success: boolean
  message: string
  data: HistoryItem[]
  total: number
}

export interface TargetItem {
  id: number
  name: string
  chinese_name: string
  description: string | null
}

export interface TargetListResponse {
  success: boolean
  message: string
  data: TargetItem[]
}

export interface ModelMetadata {
  name: string
  version: string
  created_at: string
  description: string | null
  metrics: Record<string, unknown> | null
  config: Record<string, unknown> | null
}

export interface ModelItem {
  object_name: string
  metadata: ModelMetadata | null
  public_url: string
}

export interface ModelListResponse {
  success: boolean
  message: string
  data: ModelItem[]
  latest: ModelItem | null
}

export interface CurrentModelResponse {
  success: boolean
  message: string
  data: ModelItem
}

export interface UserRegisterRequest {
  username: string
  email: string
  password: string
  nickname?: string
}

export interface UserLoginRequest {
  username: string
  password: string
}

export interface UserResponse {
  success: boolean
  message: string
  data: {
    id: string
    username: string
    email: string
    nickname: string
    role: string
    avatar_url?: string
  } | null
}