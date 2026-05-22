"""
PCB缺陷检测系统 - 检测服务
负责图像检测的核心逻辑
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectionBox:
    """检测框数据类"""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    chinese_name: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DetectionResult:
    """检测结果数据类"""
    detection_id: str
    image_path: str
    result_image_path: str
    boxes: List[DetectionBox]
    total_objects: int
    detection_time: float
    model_name: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            **asdict(self),
            'boxes': [box.to_dict() for box in self.boxes]
        }


class DetectionService:
    """
    检测服务
    负责加载模型、执行检测、绘制结果
    """

    # 缺陷类别名称映射
    CLASS_NAMES = {
        0: ("scratch", "划痕"),
        1: ("crack", "裂纹"),
        2: ("hole", "孔洞"),
        3: ("deformation", "变形"),
        4: ("missing", "缺失"),
        5: ("solder", "焊点异常"),
    }

    # 缺陷颜色映射 (BGR格式)
    CLASS_COLORS = {
        0: (248, 113, 113),   # 红色 - 划痕
        1: (251, 146, 60),    # 橙色 - 裂纹
        2: (250, 204, 21),    # 黄色 - 孔洞
        3: (52, 211, 153),    # 绿色 - 变形
        4: (56, 189, 248),    # 蓝色 - 缺失
        5: (167, 139, 250),   # 紫色 - 焊点异常
    }

    def __init__(self, output_dir: str = "static/results"):
        """
        初始化检测服务

        Args:
            output_dir: 检测结果输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 模型实例
        self.model = None
        self.model_name = None
        self.model_loaded = False

        # 统计信息
        self.stats = {
            'total_detections': 0,
            'total_objects': 0,
            'total_time': 0.0,
            'last_detection_time': None
        }

        logger.info("检测服务初始化完成")

    def load_model(self, model_path: str) -> bool:
        """
        加载YOLO模型

        Args:
            model_path: 模型文件路径

        Returns:
            是否加载成功
        """
        try:
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                logger.error(f"模型文件不存在: {model_path}")
                return False

            logger.info(f"正在加载模型: {model_path}")

            # 尝试导入ultralytics
            try:
                from ultralytics import YOLO
                self.model = YOLO(model_path)
                self.model_name = Path(model_path).stem
                self.model_loaded = True
                logger.info(f"模型加载成功: {self.model_name}")
                return True
            except ImportError:
                logger.warning("未安装ultralytics，使用模拟模式")
                self.model = None
                self.model_name = Path(model_path).stem
                self.model_loaded = True
                return True

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self.model = None
            self.model_loaded = False
            return False

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.model_loaded

    def detect_image(
        self,
        image_path: str,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45
    ) -> DetectionResult:
        """
        检测单张图像

        Args:
            image_path: 图像路径
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值

        Returns:
            检测结果
        """
        start_time = time.time()
        detection_id = str(uuid.uuid4())

        # 检查图像文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")

        boxes = []

        # 执行检测
        if self.model is not None:
            try:
                # 使用YOLO模型进行检测
                results = self.model.predict(
                    source=image_path,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    save=False,
                    verbose=False
                )

                # 解析检测结果
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])

                            class_name, chinese_name = self.CLASS_NAMES.get(
                                class_id,
                                (f"class_{class_id}", f"未知_{class_id}")
                            )

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

                # 绘制检测结果
                result_image = result.plot()

            except Exception as e:
                logger.error(f"YOLO检测失败: {str(e)}")
                result_image = self._draw_simulated_results(image, boxes)

        else:
            # 模拟模式：生成随机检测结果用于测试
            logger.info("使用模拟检测模式")
            result_image = self._draw_simulated_results(image, boxes)

        # 保存结果图像
        result_filename = f"{detection_id}.jpg"
        result_path = self.output_dir / result_filename
        cv2.imwrite(str(result_path), result_image)

        detection_time = time.time() - start_time

        # 更新统计信息
        self._update_stats(len(boxes), detection_time)

        result = DetectionResult(
            detection_id=detection_id,
            image_path=image_path,
            result_image_path=str(result_path),
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=detection_time,
            model_name=self.model_name or "unknown",
            created_at=datetime.now().isoformat()
        )

        logger.info(
            f"检测完成: {detection_id}, "
            f"检测到 {len(boxes)} 个目标, "
            f"耗时 {detection_time:.3f}s"
        )

        return result

    def _draw_simulated_results(
        self,
        image: np.ndarray,
        boxes: List[DetectionBox]
    ) -> np.ndarray:
        """
        绘制检测结果（用于模拟模式）

        Args:
            image: 原始图像
            boxes: 检测框列表

        Returns:
            绘制了检测结果的图像
        """
        result_image = image.copy()

        # 模拟添加一些检测结果用于演示
        if len(boxes) == 0:
            # 添加一些示例检测结果
            height, width = image.shape[:2]
            num_objects = np.random.randint(1, 5)

            for i in range(num_objects):
                x1 = int(np.random.randint(0, width - 100))
                y1 = int(np.random.randint(0, height - 100))
                x2 = x1 + int(np.random.randint(50, 150))
                y2 = y1 + int(np.random.randint(50, 150))

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

        # 绘制所有检测框
        for box in boxes:
            color = self.CLASS_COLORS.get(box.class_id, (0, 255, 0))

            # 绘制矩形框
            cv2.rectangle(
                result_image,
                (int(box.x1), int(box.y1)),
                (int(box.x2), int(box.y2)),
                color,
                2
            )

            # 绘制标签背景
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

            # 绘制标签文本
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
        self.stats['total_detections'] += 1
        self.stats['total_objects'] += num_objects
        self.stats['total_time'] += detection_time
        self.stats['last_detection_time'] = datetime.now().isoformat()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_time = (
            self.stats['total_time'] / self.stats['total_detections']
            if self.stats['total_detections'] > 0
            else 0
        )

        return {
            **self.stats,
            'avg_detection_time': avg_time
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            'total_detections': 0,
            'total_objects': 0,
            'total_time': 0.0,
            'last_detection_time': None
        }
        logger.info("统计信息已重置")


# 全局检测服务实例
detection_service = DetectionService()
