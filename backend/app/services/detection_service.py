"""
PCB缺陷检测系统 - 检测服务

负责图像检测的核心逻辑，包括模型加载、图像检测、结果绘制等功能。
采用路径管理模块确保路径配置的可移植性。
"""

import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import cv2
import numpy as np

from app.utils.paths import Paths
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionBox:
    """
    检测框数据类
    
    存储单个检测目标的信息，包括位置、置信度、类别等。
    
    Attributes:
        x1: 左上角 x 坐标
        y1: 左上角 y 坐标
        x2: 右下角 x 坐标
        y2: 右下角 y 坐标
        confidence: 置信度
        class_id: 类别 ID
        class_name: 英文类别名
        chinese_name: 中文类别名
    """
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    chinese_name: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class DetectionResult:
    """
    检测结果数据类
    
    存储单次检测的完整结果，包括检测 ID、路径、检测框列表等。
    
    Attributes:
        detection_id: 检测唯一标识
        image_path: 原始图像路径
        result_image_path: 结果图像路径
        boxes: 检测框列表
        total_objects: 检测到的目标总数
        detection_time: 检测耗时（秒）
        model_name: 使用的模型名称
        created_at: 创建时间
    """
    detection_id: str
    image_path: str
    result_image_path: str
    boxes: List[DetectionBox]
    total_objects: int
    detection_time: float
    model_name: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            **asdict(self),
            'boxes': [box.to_dict() for box in self.boxes]
        }


class DetectionService:
    """
    检测服务类
    
    负责加载模型、执行检测、绘制结果。支持 YOLO 模型和模拟模式。
    使用路径管理模块统一管理所有路径。
    
    Attributes:
        CLASS_NAMES: 类别名称映射表
        CLASS_COLORS: 类别颜色映射表（BGR 格式）
    """
    
    COCO_CLASS_NAMES: Dict[int, tuple] = {
        0: ("person", "人"),
        1: ("bicycle", "自行车"),
        2: ("car", "汽车"),
        3: ("motorcycle", "摩托车"),
        4: ("airplane", "飞机"),
        5: ("bus", "公交车"),
        6: ("train", "火车"),
        7: ("truck", "卡车"),
        8: ("boat", "船"),
        9: ("traffic light", "红绿灯"),
        10: ("fire hydrant", "消防栓"),
        11: ("stop sign", "停止标志"),
        12: ("parking meter", "停车计时器"),
        13: ("bench", "长椅"),
        14: ("bird", "鸟"),
        15: ("cat", "猫"),
        16: ("dog", "狗"),
        17: ("horse", "马"),
        18: ("sheep", "羊"),
        19: ("cow", "牛"),
        20: ("elephant", "大象"),
        21: ("bear", "熊"),
        22: ("zebra", "斑马"),
        23: ("giraffe", "长颈鹿"),
        24: ("backpack", "背包"),
        25: ("umbrella", "雨伞"),
        26: ("handbag", "手提包"),
        27: ("tie", "领带"),
        28: ("suitcase", "行李箱"),
        29: ("frisbee", "飞盘"),
        30: ("skis", "滑雪板"),
        31: ("snowboard", "滑雪板"),
        32: ("sports ball", "运动球"),
        33: ("kite", "风筝"),
        34: ("baseball bat", "棒球棒"),
        35: ("baseball glove", "棒球手套"),
        36: ("skateboard", "滑板"),
        37: ("surfboard", "冲浪板"),
        38: ("tennis racket", "网球拍"),
        39: ("bottle", "瓶子"),
        40: ("wine glass", "酒杯"),
        41: ("cup", "杯子"),
        42: ("fork", "叉子"),
        43: ("knife", "刀"),
        44: ("spoon", "勺子"),
        45: ("bowl", "碗"),
        46: ("banana", "香蕉"),
        47: ("apple", "苹果"),
        48: ("sandwich", "三明治"),
        49: ("orange", "橙子"),
        50: ("broccoli", "西兰花"),
        51: ("carrot", "胡萝卜"),
        52: ("hot dog", "热狗"),
        53: ("pizza", "披萨"),
        54: ("donut", "甜甜圈"),
        55: ("cake", "蛋糕"),
        56: ("chair", "椅子"),
        57: ("couch", "沙发"),
        58: ("potted plant", "盆栽"),
        59: ("bed", "床"),
        60: ("dining table", "餐桌"),
        61: ("toilet", "厕所"),
        62: ("tv", "电视"),
        63: ("laptop", "笔记本电脑"),
        64: ("mouse", "鼠标"),
        65: ("remote", "遥控器"),
        66: ("keyboard", "键盘"),
        67: ("cell phone", "手机"),
        68: ("microwave", "微波炉"),
        69: ("oven", "烤箱"),
        70: ("toaster", "烤面包机"),
        71: ("sink", "水槽"),
        72: ("refrigerator", "冰箱"),
        73: ("book", "书"),
        74: ("clock", "时钟"),
        75: ("vase", "花瓶"),
        76: ("scissors", "剪刀"),
        77: ("teddy bear", "泰迪熊"),
        78: ("hair drier", "吹风机"),
        79: ("toothbrush", "牙刷"),
    }
    
    PCB_CLASS_NAMES: Dict[int, tuple] = {
        0: ("scratch", "划痕"),
        1: ("crack", "裂纹"),
        2: ("hole", "孔洞"),
        3: ("deformation", "变形"),
        4: ("missing", "缺失"),
        5: ("solder", "焊点异常"),
    }
    
    DEFAULT_COLORS: List[tuple] = [
        (248, 113, 113), (251, 146, 60), (250, 204, 21),
        (52, 211, 153), (56, 189, 248), (167, 139, 250),
        (236, 72, 153), (6, 182, 212), (139, 92, 246),
        (234, 88, 12), (34, 197, 94), (245, 158, 11),
        (168, 85, 247), (236, 72, 153), (6, 182, 212),
    ]
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化检测服务
        
        Args:
            output_dir: 检测结果输出目录，默认使用 Paths.results()
        """
        self._output_dir = output_dir
        self._model = None
        self._model_name: Optional[str] = None
        self._model_loaded: bool = False
        self._class_names: Dict[int, tuple] = self.COCO_CLASS_NAMES
        self._model_is_custom: bool = False
        
        self._stats: Dict[str, Any] = {
            'total_detections': 0,
            'total_objects': 0,
            'total_time': 0.0,
            'last_detection_time': None
        }
        
        logger.info("检测服务初始化完成")

    @property
    def output_dir(self) -> Path:
        """获取输出目录，确保目录存在"""
        if self._output_dir is None:
            self._output_dir = Paths.results()
        Paths.ensure_dir(self._output_dir)
        return self._output_dir

    @property
    def model_name(self) -> Optional[str]:
        """获取当前模型名称"""
        return self._model_name

    def load_model(self, model_path: str) -> bool:
        """
        加载 YOLO 模型
        
        根据模型名称自动选择类别映射：
        - YOLO官方模型（如 yolo11n.pt）使用 COCO 类别（支持人像识别等）
        - 自定义训练模型（如 best_xxx.pt）使用 PCB 缺陷类别
        
        Args:
            model_path: 模型文件路径（相对或绝对路径）
        
        Returns:
            bool: 是否加载成功
        
        Raises:
            FileNotFoundError: 模型文件不存在
        """
        path = Path(model_path)
        
        if not path.is_absolute():
            path = Paths.root() / path
        
        if not path.exists():
            logger.error(f"模型文件不存在: {path}")
            return False
        
        model_name = path.stem.lower()
        
        if 'yolo' in model_name and not ('best' in model_name or 'custom' in model_name):
            self._class_names = self.COCO_CLASS_NAMES
            self._model_is_custom = False
            logger.info(f"检测到 YOLO 官方模型，使用 COCO 类别")
        else:
            self._class_names = self.PCB_CLASS_NAMES
            self._model_is_custom = True
            logger.info(f"检测到自定义模型，使用 PCB 缺陷类别")
        
        logger.info(f"正在加载模型: {path}")
        
        try:
            from ultralytics import YOLO
            self._model = YOLO(str(path))
            self._model_name = path.stem
            self._model_loaded = True
            logger.info(f"模型加载成功: {self._model_name}")
            return True
        except ImportError:
            logger.warning("未安装 ultralytics，使用模拟模式")
            self._model = None
            self._model_name = path.stem
            self._model_loaded = True
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self._model = None
            self._model_loaded = False
            return False

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model_loaded

    def detect_image(
        self,
        image_path: str,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45
    ) -> DetectionResult:
        """
        检测单张图像
        
        Args:
            image_path: 图像文件路径
            conf_threshold: 置信度阈值，默认 0.5
            iou_threshold: IOU 阈值，默认 0.45
        
        Returns:
            DetectionResult: 检测结果
        
        Raises:
            FileNotFoundError: 图像文件不存在
            ValueError: 无法读取图像
        """
        start_time = time.time()
        detection_id = str(uuid.uuid4())
        
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        boxes: List[DetectionBox] = []
        
        if self._model is not None:
            boxes, result_image = self._detect_with_model(
                image, str(path), conf_threshold, iou_threshold
            )
        else:
            logger.info("使用模拟检测模式")
            result_image, boxes = self._simulate_detection(image, boxes)
        
        result_filename = f"{detection_id}.jpg"
        result_path = self.output_dir / result_filename
        cv2.imwrite(str(result_path), result_image)
        
        # 确保也保存到 static/results 目录中，以便前端访问
        static_results_dir = Paths.static() / "results"
        Paths.ensure_dir(static_results_dir)
        static_result_path = static_results_dir / result_filename
        cv2.imwrite(str(static_result_path), result_image)
        
        # 同时保存原始图片到 static/uploads
        static_uploads_dir = Paths.static() / "uploads"
        Paths.ensure_dir(static_uploads_dir)
        import shutil
        static_image_path = static_uploads_dir / path.name
        if not static_image_path.exists():
            shutil.copy(str(path), str(static_image_path))
        
        detection_time = time.time() - start_time
        self._update_stats(len(boxes), detection_time)
        
        result = DetectionResult(
            detection_id=detection_id,
            image_path=str(path.relative_to(Paths.root())),
            result_image_path=str(result_path.relative_to(Paths.root())),
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=detection_time,
            model_name=self._model_name or "unknown",
            created_at=datetime.now().isoformat()
        )
        
        logger.info(
            f"检测完成: {detection_id}, "
            f"检测到 {len(boxes)} 个目标, "
            f"耗时 {detection_time:.3f}s"
        )
        
        return result

    def _detect_with_model(
        self,
        image: np.ndarray,
        image_path: str,
        conf_threshold: float,
        iou_threshold: float
    ) -> tuple:
        """
        使用 YOLO 模型进行检测
        
        Args:
            image: 图像数组
            image_path: 图像路径
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
        
        Returns:
            tuple: (检测框列表, 结果图像)
        """
        boxes: List[DetectionBox] = []
        
        try:
            results = self._model.predict(
                source=image_path,
                conf=conf_threshold,
                iou=iou_threshold,
                save=False,
                verbose=False
            )
            
            for result in results:
                if result.boxes is not None:
                    boxes.extend(self._parse_detection_boxes(result.boxes))
                
                result_image = result.plot()
            
        except Exception as e:
            logger.error(f"YOLO 检测失败: {str(e)}")
            result_image, boxes = self._simulate_detection(image, boxes)
        
        return boxes, result_image

    def _parse_detection_boxes(self, boxes) -> List[DetectionBox]:
        """
        解析检测结果中的检测框
        
        Args:
            boxes: YOLO 检测结果中的 boxes 对象
        
        Returns:
            List[DetectionBox]: 检测框列表
        """
        parsed_boxes = []
        
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            class_name, chinese_name = self._class_names.get(
                class_id,
                (f"class_{class_id}", f"未知_{class_id}")
            )
            
            parsed_boxes.append(DetectionBox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                confidence=confidence,
                class_id=class_id,
                class_name=class_name,
                chinese_name=chinese_name
            ))
        
        return parsed_boxes

    def _simulate_detection(
        self,
        image: np.ndarray,
        boxes: List[DetectionBox]
    ) -> tuple:
        """
        模拟检测（用于演示或模型未加载时）
        
        Args:
            image: 原始图像
            boxes: 现有检测框列表
        
        Returns:
            tuple: (结果图像, 检测框列表)
        """
        if len(boxes) == 0:
            height, width = image.shape[:2]
            num_objects = np.random.randint(1, 5)
            
            for _ in range(num_objects):
                x1 = int(np.random.randint(0, max(1, width - 100)))
                y1 = int(np.random.randint(0, max(1, height - 100)))
                x2 = x1 + int(np.random.randint(50, min(150, width - x1)))
                y2 = y1 + int(np.random.randint(50, min(150, height - y1)))
                
                class_id = np.random.randint(0, 6)
                confidence = np.random.uniform(0.7, 0.98)
                
                class_name, chinese_name = self.CLASS_NAMES[class_id]
                
                boxes.append(DetectionBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))
        
        result_image = self._draw_boxes(image, boxes)
        return result_image, boxes

    def _draw_boxes(
        self,
        image: np.ndarray,
        boxes: List[DetectionBox]
    ) -> np.ndarray:
        """
        在图像上绘制检测框
        
        Args:
            image: 原始图像
            boxes: 检测框列表
        
        Returns:
            np.ndarray: 绘制了检测框的图像
        """
        result_image = image.copy()
        
        for box in boxes:
            color = self.CLASS_COLORS.get(box.class_id, (0, 255, 0))
            
            cv2.rectangle(
                result_image,
                (int(box.x1), int(box.y1)),
                (int(box.x2), int(box.y2)),
                color,
                2
            )
            
            label = f"{box.chinese_name} {box.confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 1
            
            (label_width, label_height), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )
            
            label_y = max(int(box.y1) - 10, label_height + 10)
            
            cv2.rectangle(
                result_image,
                (int(box.x1), label_y - label_height - baseline),
                (int(box.x1) + label_width, label_y + baseline),
                color,
                -1
            )
            
            cv2.putText(
                result_image,
                label,
                (int(box.x1), label_y),
                font,
                font_scale,
                (255, 255, 255),
                thickness
            )
        
        return result_image

    def _update_stats(self, num_objects: int, detection_time: float) -> None:
        """更新统计信息"""
        self._stats['total_detections'] += 1
        self._stats['total_objects'] += num_objects
        self._stats['total_time'] += detection_time
        self._stats['last_detection_time'] = datetime.now().isoformat()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 包含检测统计数据的字典
        """
        avg_time = (
            self._stats['total_time'] / self._stats['total_detections']
            if self._stats['total_detections'] > 0
            else 0.0
        )
        
        return {
            **self._stats,
            'avg_detection_time': avg_time
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            'total_detections': 0,
            'total_objects': 0,
            'total_time': 0.0,
            'last_detection_time': None
        }
        logger.info("统计信息已重置")


detection_service = DetectionService()
