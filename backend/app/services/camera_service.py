"""
PCB缺陷检测系统 - 摄像头检测服务

负责实时摄像头流检测的核心逻辑，支持使用通用YOLO模型进行实时目标检测。
采用路径管理模块确保路径配置的可移植性。
"""

import time
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from app.utils.paths import Paths
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CameraDetectionResult:
    """
    摄像头检测结果数据类
    
    存储单次摄像头帧检测的结果。
    
    Attributes:
        frame_id: 帧唯一标识
        timestamp: 检测时间戳
        boxes: 检测框列表
        total_objects: 检测到的目标总数
        frame_width: 帧宽度
        frame_height: 帧高度
        model_name: 使用的模型名称
        inference_time: 推理耗时（毫秒）
    """
    frame_id: str
    timestamp: str
    boxes: List[Dict[str, Any]]
    total_objects: int
    frame_width: int
    frame_height: int
    model_name: str
    inference_time: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class CameraDetectionService:
    """
    摄像头检测服务类
    
    负责加载YOLO模型、捕获摄像头帧、执行实时检测、绘制结果。
    支持使用通用YOLO模型（如yolo11n.pt）进行基础目标检测。
    
    Attributes:
        COCO_CLASS_NAMES: COCO数据集类别名称列表
        COCO_CLASS_COLORS: 类别颜色映射表（BGR格式）
    """
    
    COCO_CLASS_NAMES = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
        "truck", "boat", "traffic light", "fire hydrant", "stop sign",
        "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
        "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
        "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
        "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
        "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
        "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
        "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
        "couch", "potted plant", "bed", "dining table", "toilet", "tv",
        "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
        "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
        "scissors", "teddy bear", "hair drier", "toothbrush"
    ]
    
    COCO_CLASS_COLORS: Dict[int, Tuple[int, int, int]] = {
        i: tuple(np.random.randint(0, 256, size=3).tolist()) 
        for i in range(len(COCO_CLASS_NAMES))
    }

    def __init__(self):
        """初始化摄像头检测服务"""
        self._model = None
        self._model_name: Optional[str] = None
        self._model_loaded: bool = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_running: bool = False
        
        self._stats: Dict[str, Any] = {
            'total_frames': 0,
            'total_objects': 0,
            'total_time': 0.0,
            'avg_fps': 0.0,
            'last_frame_time': None
        }
        
        logger.info("摄像头检测服务初始化完成")

    @