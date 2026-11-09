import pytest
import numpy as np
import cv2
from pathlib import Path
import image_processing.adaptive_preprocessing as ap
import image_processing.ocr as ocr

IMAGES_DIR = Path(__file__).parent / "images"
WIKI_PHOTOS_DIR = IMAGES_DIR / "wikipedia_photos"
PAINT_TEXT_DIR = IMAGES_DIR / "paint_text"

def open_image(image_path: Path):
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Image not found at {image_path}")
    return img

# region # Fixtures / Blurry Text

@pytest.fixture
def dummy_image():
    img = np.full((200, 500), 0, dtype=np.uint8)
    cv2.putText(img, "Hello World! 123", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, 255, 2)
    cv2.putText(img, "Testing Blur Reduction", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 255, 2)
    return img

@pytest.fixture
def blur_3_image(dummy_image):
    return cv2.GaussianBlur(dummy_image, (5, 5), 0)

@pytest.fixture
def blur_19_image(dummy_image):
    return cv2.GaussianBlur(dummy_image, (19, 19), 0)

# endregion

# region # Fixtures / Wiki Photos

@pytest.fixture
def light_inclined_wiki_photo():
    return open_image(WIKI_PHOTOS_DIR / "PXL_20261108_144936240.jpg")

@pytest.fixture
def dark_radial_blur_wiki_photo():
    return open_image(WIKI_PHOTOS_DIR / "IMG_20261108_165232.jpg")

# endregion

# region # Fixtures / Paint Text

@pytest.fixture
def diagonal_big_paint_photo():
    return open_image(PAINT_TEXT_DIR / "diagonal_big.jpg")

@pytest.fixture
def diagonal_small_paint_photo():
    return open_image(PAINT_TEXT_DIR / "diagonal_small.jpg")

@pytest.fixture
def dimmed_paint_photo():
    return open_image(PAINT_TEXT_DIR / "dimmed.jpg")

@pytest.fixture
def overexposed_paint_photo():
    return open_image(PAINT_TEXT_DIR / "overexposed.jpg")

@pytest.fixture
def text_test_paint_photo():
    return open_image(PAINT_TEXT_DIR / "text_test,png.png")

# endregion



def show_images(images: list[tuple[str, np.ndarray]]) -> None:
    for title, img in images: cv2.imshow(title, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test_adaptive_blur_reduction(dummy_image, blur_3_image, blur_19_image):
    reduced_blur_0 = ap.try_reduce_blur(dummy_image)
    reduced_blur_3 = ap.try_reduce_blur(blur_3_image)
    reduced_blur_19 = ap.try_reduce_blur(blur_19_image)
    show_images([
        ("reduced_blur_0", reduced_blur_0),
        ("reduced_blur_3", reduced_blur_3),
        ("reduced_blur_19", reduced_blur_19),
    ])
    assert np.array_equal(reduced_blur_0, dummy_image)
    assert np.array_equal(reduced_blur_3, blur_3_image)
    assert not np.array_equal(reduced_blur_19, blur_19_image)

def test_wiki_hist_eq_ocr(dimmed_paint_photo):
    light = ap.correct_exposure(dimmed_paint_photo)
    show_images([
        ("light", light),
    ])
    
    _, scores_original = zip(*ocr.get_polygons(dimmed_paint_photo))
    _, scores_processed = zip(*ocr.get_polygons(light))
    
    print(f"scores_original {scores_original}")
    print(f"scores_processed {scores_processed}")
    
    diff = np.array(scores_processed) - np.array(scores_original)
    assert np.all(diff > 0.10)

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (5, 5, 10),
    (-1, 1, 0),
])
def test_parametrized_addition(a, b, expected):
    assert a + b == expected
