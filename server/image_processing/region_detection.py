from uuid import uuid4
from time import monotonic
import numpy as np
from . import ocr
from .optical_flow import optical_flow
from .region import Region
from .tracking import match_polygons
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
    optical_flow.reset()

def proc(image: np.ndarray) -> list[dict]:
    processed_image = ap.adaptive_preprocessing(image)

    # Mutam poligoanele vechi odata cu camera inainte sa facem matching-ul
    M = optical_flow.estimate_motion(processed_image)
    if M is not None and regions:
        for region in regions.values():
            region.apply_transform(M)

    # Salvam mai intai toate poligoanele si scorurile
    # ca sa putem aplica Hungarian matching raportat la toate.
    detected = [
        (np.asarray(polygon, dtype=np.int32), float(score))
        for polygon, score in ocr.get_polygons(processed_image)
        if score >= 0.70
    ]
    
    # Pacem match intre poligoanele existente si cele detectate.
    existing_ids = list(regions.keys())
    matched, unmatched_existing, unmatched_detected = match_polygons(
        [regions[region_id].polygon for region_id in existing_ids],
        [polygon for polygon, _ in detected],
    )

    # Le actualizam pe cele care s-au schimbat
    for r, c in matched:
        polygon, score = detected[c]
        regions[existing_ids[r]].update_region(polygon, score)

    # Le stergem pe cele care au disparut
    for r in unmatched_existing:
        del regions[existing_ids[r]]

    # Si le adaugam pe cele noi aparute
    new_polygons = [detected[c] for c in unmatched_detected]
    polygon_images = [polygon for polygon, _ in new_polygons]
    new_texts = ocr.ocr(processed_image, polygon_images)
    report_text_recognition_rate(1 if polygon_images else 0)
    for (polygon, score), text in zip(new_polygons, new_texts):
        region_id = uuid4().hex
        regions[region_id] = Region(polygon, text, region_id, score)

    for region in regions.values():
        region.request_translation()

    return [region.to_payload() for region in regions.values()]
