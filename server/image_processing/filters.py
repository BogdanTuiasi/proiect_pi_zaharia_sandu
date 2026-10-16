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
