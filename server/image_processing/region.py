from typing import Optional
import random
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .translator import translator

CENTER_THR = 100
CUMULATIVE_POINT_THR = CENTER_THR


def draw_text_in_polygon(
    image: np.ndarray,
    polygon: np.ndarray,
    text: str,
    color = (255, 255, 255)
):
    pts = polygon.reshape(-1, 2).astype(np.float32)
    cv2.fillPoly(image, [polygon], color)

    w = int(np.linalg.norm(pts[1] - pts[0]))
    h = int(np.linalg.norm(pts[3] - pts[0]))

    font_size = max(10, int(h * 0.7))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    patch = Image.new("RGB", (w, h), color)
    draw = ImageDraw.Draw(patch)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if tw > w and tw > 0:
        font_size = max(8, int(font_size * (w / tw)))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    tx = (w - tw) // 2 - bbox[0]
    ty = (h - th) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=(0, 0, 0))

    src_pts = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    tfm = cv2.getPerspectiveTransform(src_pts, pts)
    cv2.warpPerspective(np.array(patch), tfm, (image.shape[1], image.shape[0]), dst=image, borderMode=cv2.BORDER_TRANSPARENT)


class Region:
    """Se ocupa de controlul informatiilor de desenare a regiunii"""
    __polygon: np.ndarray[tuple[int, int]]
    __text: str
    __translation: Optional[str] = None
    __is_translating: bool = False
    
    __region_id: str # for debugging
    
    def __is_same(self, other_polygon: np.ndarray[tuple[int, int]]) -> bool:
        """Daca centrul e aproximativ acelasi, si pozitia e aproximativ aceeasi, atunci probabil e aceeasi regiune."""
        c1 = np.average(self.__polygon, axis=0)
        c2 = np.average(other_polygon, axis=0)
        d = np.linalg.norm(c1 - c2)
        if(d > CENTER_THR): return False
        d = np.sum(np.linalg.norm(self.__polygon - other_polygon, axis=1), axis=0)
        return d <= CUMULATIVE_POINT_THR
    
    def update_region(self, other_polygon: np.ndarray[tuple[int, int]], score: float) -> bool:
        if(not self.__is_same(other_polygon)): return False
        self.__polygon = other_polygon
        return True
        
    def __init__(self, polygon: np.ndarray[tuple[int, int]], text: str, region_id: str):
        self.__polygon = polygon
        self.__text = text
        self.__region_id = region_id

    def set_translation(self, text: str):
        # daca intre timp stergem traducerea sa nu traduca peste eronat
        if(not self.__is_translating): return
        self.__translation = text
        self.__is_translating = False
        
    def erase_translation(self):
        self.__translation = None
        self.__is_translating = False
        
    def draw(self, image: np.ndarray):
        if self.__translation is None and not self.__is_translating:
            self.__is_translating = True
            translator.translate_async(self.__text, self.set_translation)

        if not self.__translation:
            return

        rng = random.Random(self.__region_id)
        color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        draw_text_in_polygon(image, self.__polygon, self.__translation, color)
