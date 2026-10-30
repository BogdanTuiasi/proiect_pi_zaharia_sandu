import cv2
import numpy as np
from paddleocr import TextDetection

def make_contrast_lut(a, b, sa, sb, L=256):
    """Creaza un Look-up Table (tabel de rezultate) pentru un filtru de contrast rapid."""
    
    m = sa / a
    n = (sb - sa) / (b - a)
    p = (L - 1 - sb) / (L - 1 - b)
    
    lut = np.array([
        m * v if v < a else
        sa + n * (v - a) if v < b else
        sb + p * (v - b)
        for v in range(L)
    ])

    return np.clip(lut, 0, 255).astype(np.uint8)


def accentuate_contrast(a, b, sa, sb, L=256):
    lut = make_contrast_lut(a, b, sa, sb, L)
    return lambda image: cv2.LUT(image, lut)

detector = TextDetection(
    model_name="PP-OCRv5_mobile_det",
    device="cpu",
    enable_mkldnn=False,
)

def proc(image: np.ndarray):
    regions = []

    for result in detector.predict(image):
        for polygon, score in zip(result["dt_polys"], result["dt_scores"]):
            regions.append({
                "polygon": polygon.tolist(),
                "score": float(score),
            })

            points = np.asarray(polygon, dtype=np.int32).reshape(-1, 1, 2)
            cv2.polylines(image, [points], True, (0, 255, 0), 2)
    print(regions)
    return image
