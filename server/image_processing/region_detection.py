from uuid import uuid4
from time import monotonic
import numpy as np
from . import ocr
from .region import Region
import image_processing.adaptive_preprocessing as ap

regions: dict[str, Region] = {}
_recognition_count_this_second = 0
_recognition_per_second_total = 0
_recognition_seconds = 0
_recognition_window_started = monotonic()


def report_text_recognition_rate(recognition_count: int) -> None:
    global _recognition_count_this_second
    global _recognition_per_second_total, _recognition_seconds
    global _recognition_window_started

    _recognition_count_this_second += recognition_count
    now = monotonic()
    elapsed = now - _recognition_window_started
    if elapsed >= 1.0:
        seconds = max(1, int(elapsed))
        _recognition_per_second_total += _recognition_count_this_second
        _recognition_seconds += seconds
        mean = _recognition_per_second_total / _recognition_seconds
        print(
            f"OCR text recognition: {_recognition_count_this_second / elapsed:.2f}/s "
            f"(media cumulativa: {mean:.2f}/s)",
            flush=True,
        )
        _recognition_count_this_second = 0
        _recognition_window_started = now

def reset_regions():
    regions.clear()

def proc(image: np.ndarray) -> list[dict]:
    processed_image = ap.adaptive_preprocessing(image)

    update_pending = set(regions.keys())
    new_polygons: list[tuple[np.ndarray, float]] = []
    for polygon, score in ocr.get_polygons(processed_image):
        if score < 0.70: continue

        polygon = np.asarray(polygon, dtype=np.int32)
        for region_id in update_pending:
            if regions[region_id].update_region(polygon, score): break
        else: region_id = None

        if region_id is not None:
            update_pending.discard(region_id)
        else:
            new_polygons.append((polygon, float(score)))

    polygon_images = [polygon for polygon, _ in new_polygons]
    new_texts = ocr.ocr(processed_image, polygon_images)
    report_text_recognition_rate(1 if polygon_images else 0)
    for (polygon, score), text in zip(new_polygons, new_texts):
        region_id = uuid4().hex
        regions[region_id] = Region(polygon, text, region_id, score)

    for lost_region_id in update_pending:
        del regions[lost_region_id]

    for region in regions.values():
        region.request_translation()

    return [region.to_payload() for region in regions.values()]
