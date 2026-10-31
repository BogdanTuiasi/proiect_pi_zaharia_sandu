import cv2
import numpy as np
from paddleocr import TextRecognition

recognizer = TextRecognition(
    model_name="PP-OCRv5_mobile_rec",
    device="gpu:0",
)

def ocr(image: np.ndarray, polygon: np.ndarray) -> str:
    tl, tr, br, bl = np.asarray(polygon, dtype=np.float32).reshape(4, 2)

    width = max(2, round(max(
        np.linalg.norm(tr - tl),
        np.linalg.norm(br - bl),
    )))
    height = max(2, round(max(
        np.linalg.norm(bl - tl),
        np.linalg.norm(br - tr),
    )))

    source = np.array([tl, tr, br, bl], dtype=np.float32)
    destination = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1],
    ], dtype=np.float32)

    transform = cv2.getPerspectiveTransform(source, destination)
    crop = cv2.warpPerspective(image, transform, (width, height))

    result = recognizer.predict(crop)[0]
    return result["rec_text"]
