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
