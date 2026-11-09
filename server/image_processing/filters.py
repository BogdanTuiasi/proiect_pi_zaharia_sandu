import cv2
import numpy as np

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

def sharpen_laplacian(img: np.ndarray, strength: float = 1.0) -> np.ndarray:
    kernel = np.array([
        [0, -strength, 0],
        [-strength, 1 + 4 * strength, -strength],
        [0, -strength, 0]
    ], dtype=np.float32)
    filtered = cv2.filter2D(img.astype(np.float32), -1, kernel)
    return np.clip(filtered, 0, 255).astype(np.uint8)

def sharpen_unsharp_mask(img: np.ndarray, sigma: float = 3.0, strength: float = 2.0) -> np.ndarray:
    low_freq = cv2.GaussianBlur(img, (0, 0), sigmaX=sigma)
    sharp = cv2.addWeighted(img, 1.0 + strength, low_freq, -strength, 0)
    return sharp

def estimate_blur(image: np.ndarray, threshold: float = 100.0) -> tuple[bool, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return (score < threshold, score)

# lab 3, cu OpenCV

def apply_lab(fn):
    def wrapper(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2: return fn(image)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_eq = fn(l)
        lab_eq = cv2.merge((l_eq, a, b))
        return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
    return wrapper

def histogram_equalization(image: np.ndarray) -> np.ndarray:
    return apply_lab(cv2.equalizeHist)(image)

def clahe_adaptive_equalization(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return apply_lab(clahe.apply)(image)

def eg_adapt_img_lab(img: np.ndarray, n: int = 15, L: int = 256) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = gray.shape
    pad = n // 2
    padded = cv2.copyMakeBorder(gray, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    result = np.zeros((h, w), dtype=np.uint8)

    for y in range(h):
        for x in range(w):
            subreg = padded[y:y + n, x:x + n]
            hh = np.bincount(subreg.ravel(), minlength=L)
            hn = hh / (n * n)
            hc = np.cumsum(hn)
            center_val = gray[y, x]
            value = int(np.floor((L - 1) * hc[center_val]))
            result[y, x] = min(255, value)

    return result
