from threading import Lock
from typing import Optional
import numpy as np
from .tracking import is_same_polygon
from .translator import translator


class Region:
    """Se ocupa de controlul informatiilor de desenare a regiunii"""
    __polygon: np.ndarray[tuple[int, int]]
    __text: str
    __translation: Optional[str] = None
    __is_translating: bool = False
    
    __region_id: str # for debugging
    __score: float
    __lock: Lock
    
    def __is_same(self, other_polygon: np.ndarray) -> bool:
        return is_same_polygon(self.__polygon, other_polygon)
    
    def update_region(self, other_polygon: np.ndarray[tuple[int, int]], score: float) -> bool:
        if(not self.__is_same(other_polygon)): return False
        with self.__lock:
            self.__polygon = other_polygon
            self.__score = float(score)
        return True
        
    def __init__(
        self,
        polygon: np.ndarray[tuple[int, int]],
        text: str,
        region_id: str,
        score: float = 0.0,
    ):
        self.__polygon = polygon
        self.__text = text
        self.__region_id = region_id
        self.__score = float(score)
        self.__lock = Lock()

    def request_translation(self):
        with self.__lock:
            if self.__translation is not None or self.__is_translating:
                return
            self.__is_translating = True

        translator.translate_async(self.__text, self.set_translation)

    def set_translation(self, text: str):
        with self.__lock:
            if not self.__is_translating:
                return
            self.__translation = text
            self.__is_translating = False
        
    def erase_translation(self):
        with self.__lock:
            self.__translation = None
            self.__is_translating = False

    def to_payload(self) -> dict:
        with self.__lock:
            polygon = self.__polygon.copy()
            translation = self.__translation or ""
            translating = self.__is_translating
            score = self.__score

        return {
            "region_id": self.__region_id,
            "source_text": self.__text,
            "translation": translation,
            "translation_pending": translating,
            "score": score,
            "polygon": [
                {"x": int(point[0]), "y": int(point[1])}
                for point in polygon.reshape(-1, 2)
            ],
        }
