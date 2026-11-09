import cv2
import numpy as np
from paddleocr import TextDetection, TextRecognition

detector = TextDetection(
    model_name="PP-OCRv5_mobile_det",
    device="gpu:0",
    enable_mkldnn=False,
)

recognizer = TextRecognition(
    model_name="PP-OCRv5_mobile_rec",
    device="gpu:0",
)

def get_polygons(image: np.ndarray) -> list[tuple[np.ndarray, float]]:
    result = detector.predict(image)[0]
    return zip(result["dt_polys"], result["dt_scores"])

def __crop(image: np.ndarray, polygon: np.ndarray) -> np.ndarray:
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
    return cv2.warpPerspective(image, transform, (width, height))

def ocr(image: np.ndarray, polygons: list[np.ndarray]) -> list[str]:
    if not polygons: return []
    crops = [__crop(image, poly) for poly in polygons]
    results = recognizer.predict(crops, batch_size=32)
    return [res["rec_text"] for res in results]
