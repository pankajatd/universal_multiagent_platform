"""Project registry — maps project keys to their adapter classes."""
from __future__ import annotations
from typing import Dict, Optional, Type
from .base_adapter import BaseProjectAdapter


class ProjectRegistry:
    """Central registry of all available project adapters."""

    _adapters: Dict[str, Type[BaseProjectAdapter]] = {}
    _instances: Dict[str, BaseProjectAdapter] = {}

    @classmethod
    def register(cls, key: str, adapter_class: Type[BaseProjectAdapter]) -> None:
        cls._adapters[key] = adapter_class

    @classmethod
    def get(cls, key: str) -> Optional[BaseProjectAdapter]:
        if key not in cls._instances:
            if key in cls._adapters:
                cls._instances[key] = cls._adapters[key]()
        return cls._instances.get(key)

    @classmethod
    def list_projects(cls) -> Dict[str, Type[BaseProjectAdapter]]:
        return dict(cls._adapters)

    @classmethod
    def register_all(cls) -> None:
        """Import and register all available adapters."""
        try:
            from .industrial_adapter import IndustrialAdapter
            cls.register("industrial_vision_rag", IndustrialAdapter)
        except Exception:
            pass
        try:
            from .face_detection_adapter import FaceDetectionAdapter
            cls.register("face_detection", FaceDetectionAdapter)
        except Exception:
            pass
        try:
            from .ocr_adapter import OCRAdapter
            cls.register("ocr_system", OCRAdapter)
        except Exception:
            pass


# Auto-register all adapters when module is loaded
ProjectRegistry.register_all()
