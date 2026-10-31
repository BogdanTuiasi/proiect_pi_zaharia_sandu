from typing import Optional
import cv2
import numpy as np
from .translator import translator

CENTER_THR = 100
CUMULATIVE_POINT_THR = 100

def draw_text_in_polygon(
    image: np.ndarray,
    polygon: np.ndarray,
    text: str,
):
    x, y, w, h = cv2.boundingRect(polygon)

    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 1

    (text_w, text_h), baseline = cv2.getTextSize(text, font, 1.0, thickness)
    scale = min(
        w / max(text_w, 1),
        h / max(text_h + baseline, 1),
    )
    (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)

    origin = (
        x + (w - text_w) // 2,
        y + (h - text_h - baseline) // 2 + text_h,
    )

    cv2.fillPoly(image, [polygon], (255, 255, 255))
    cv2.putText(
        image, text, origin, font, scale,
        (0, 0, 0), thickness, cv2.LINE_AA,
    )

class Region:
    """Se ocupa de controlul informatiilor de desenare a regiunii"""
    __polygon: np.ndarray[tuple[int, int]]
    __text: str
    __translation: Optional[str] = None
    
    def __is_same(self, other_polygon: np.ndarray[tuple[int, int]]) -> bool:
        """Daca centrul e aproximativ acelasi, si pozitia e aproximativ aceeasi, atunci probabil e aceeasi regiune."""
        c1 = np.average(self.__polygon, axis=0)
        c2 = np.average(other_polygon, axis=0)
        d = np.linalg.norm(c1, c2)
        if(d > CENTER_THR): return False
        d = np.sum(np.linalg.norm(self.__polygon - other_polygon, axis=1))
        return d <= CUMULATIVE_POINT_THR
    
    def update_region(self, other_polygon: np.ndarray[tuple[int, int]], score: float) -> bool:
        if(not self.__is_same(other_polygon)): return False
        self.__polygon = other_polygon
        return True
        
    def __init__(self, polygon: np.ndarray[tuple[int, int]], text: str):
        self.__polygon = polygon
        self.__text = text
        
    def erase_translation(self):
        self.__translation = None
        
    def draw(self, image: np.ndarray):
        if(self.__translation == None):
            self.__translation = translator.translate(self.__text)
        draw_text_in_polygon(image, self.__polygon, self.__translation)
