from typing import Optional
import cv2
import numpy as np

_MAX_FLOW_WIDTH = 480
_MIN_POINTS = 8
_MIN_INLIERS = 6


# Micsoram imaginea ca sa mearga rapid optical flow-ul, si pastram scara ca sa stim cu cat impartim la final
def _resize_for_flow(gray: np.ndarray) -> tuple[np.ndarray, float]:
    h, w = gray.shape[:2]
    if w <= _MAX_FLOW_WIDTH:
        return gray, 1.0
    scale = _MAX_FLOW_WIDTH / float(w)
    small = cv2.resize(gray, (_MAX_FLOW_WIDTH, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    return small, scale


class OpticalFlow:
    def __init__(self) -> None:
        self._prev_gray: Optional[np.ndarray] = None

    def reset(self) -> None:
        self._prev_gray = None

    # Estimeaza cum s-a miscat camera fata de cadrul anterior (translatie, rotatie, zoom)
    def estimate_motion(self, image: np.ndarray) -> Optional[np.ndarray]:
        curr_gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        prev_gray = self._prev_gray
        self._prev_gray = curr_gray

        if prev_gray is None or prev_gray.shape != curr_gray.shape:
            return None

        prev_small, scale = _resize_for_flow(prev_gray)
        curr_small, _ = _resize_for_flow(curr_gray)

        # Luam cateva puncte bune de urmarit (colturi) din cadrul vechi
        pts0 = cv2.goodFeaturesToTrack(prev_small, maxCorners=200, qualityLevel=0.01, minDistance=12)
        if pts0 is None or len(pts0) < _MIN_POINTS:
            return None

        # Vedem unde au ajuns punctele acelea in cadrul nou (Lucas-Kanade)
        pts1, status, _ = cv2.calcOpticalFlowPyrLK(
            prev_small, curr_small, pts0, None, winSize=(21, 21), maxLevel=3
        )
        if pts1 is None or status is None:
            return None

        mask = status.ravel() == 1
        good_old = pts0[mask]
        good_new = pts1[mask]
        if len(good_new) < _MIN_POINTS:
            return None

        # Scoatem transformarea generala cu RANSAC ca sa ignoram punctele care au sarit
        M, inliers = cv2.estimateAffinePartial2D(
            good_old, good_new, method=cv2.RANSAC, ransacReprojThreshold=3.0
        )
        if M is None or inliers is None or int(inliers.sum()) < _MIN_INLIERS:
            return None

        # Daca zoom-ul estimat e exagerat, mai bine ignoram frame-ul decat sa stricam poligoanele
        scale_factor = float(np.hypot(M[0, 0], M[1, 0]))
        if not (0.7 <= scale_factor <= 1.4):
            return None

        # Aducem translatia inapoi la dimensiunea reala a imaginii
        M_full = M.copy()
        M_full[:, 2] /= scale
        return M_full


optical_flow = OpticalFlow()


# Aplica matricea de transformare pe colturile unui poligon
def transform_polygon(polygon: np.ndarray, M: np.ndarray) -> np.ndarray:
    pts = np.asarray(polygon, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.transform(pts, M).reshape(-1, 2)
    return np.rint(transformed).astype(np.int32)
