import numpy as np
from . import filters as fl

def try_reduce_blur(image: np.ndarray):
    is_blurry, score = fl.estimate_blur(image)
    return image if not is_blurry \
        else fl.sharpen_unsharp_mask(image, sigma=3.0, strength=2.5) if score < 100 \
        else fl.sharpen_unsharp_mask(image, sigma=2.0, strength=1.5) if score < 1000 \
        else fl.sharpen_unsharp_mask(image, sigma=1.0, strength=1.0)

def correct_exposure(image: np.ndarray):
    return fl.clahe_adaptive_equalization(image, tile_grid_size=(5, 5))
    # return fl.histogram_equalization(image)

def adaptive_preprocessing(image: np.ndarray):
    corrected = correct_exposure(image)
    blur_reduced = try_reduce_blur(corrected)
    return blur_reduced
