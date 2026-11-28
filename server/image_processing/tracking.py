import cv2
import numpy as np

IOU_THR = 0.25

def polygon_iou(poly_a: np.ndarray, poly_b: np.ndarray) -> float:
    a = np.asarray(poly_a, dtype=np.float32).reshape(-1, 2)
    b = np.asarray(poly_b, dtype=np.float32).reshape(-1, 2)
    if len(a) < 3 or len(b) < 3:
        return 0.0

    ax1, ay1 = a.min(axis=0)
    ax2, ay2 = a.max(axis=0)
    bx1, by1 = b.min(axis=0)
    bx2, by2 = b.max(axis=0)
    if ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1:
        return 0.0

    hull_a = cv2.convexHull(a)
    hull_b = cv2.convexHull(b)
    area_a = cv2.contourArea(hull_a)
    area_b = cv2.contourArea(hull_b)
    if area_a <= 0 or area_b <= 0:
        return 0.0

    inter_area, _ = cv2.intersectConvexConvex(hull_a, hull_b)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return float(inter_area / union)

def is_same_polygon(poly_a: np.ndarray, poly_b: np.ndarray) -> bool:
    a = np.asarray(poly_a, dtype=np.float32).reshape(-1, 2)
    b = np.asarray(poly_b, dtype=np.float32).reshape(-1, 2)
    wa, ha = a.max(axis=0) - a.min(axis=0)
    wb, hb = b.max(axis=0) - b.min(axis=0)
    if min(wa, wb) < 0.7 * max(wa, wb, 1.0) or min(ha, hb) < 0.6 * max(ha, hb, 1.0):
        return False
    return polygon_iou(poly_a, poly_b) >= IOU_THR
