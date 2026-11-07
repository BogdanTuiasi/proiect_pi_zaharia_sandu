from uuid import uuid4
import numpy as np
from paddleocr import TextDetection
from .ocr import ocr
from .region import Region

detector = TextDetection(
    model_name="PP-OCRv5_mobile_det",
    device="gpu:0",
    enable_mkldnn=False,
)

regions: dict[str, Region] = {}

def proc(image: np.ndarray):
    for result in detector.predict(image):
        update_pending = set(regions.keys())
        new_polygons = []
        for polygon, score in zip(result["dt_polys"], result["dt_scores"]):
            if score < 0.70: continue

            polygon = np.asarray(polygon, dtype=np.int32)
            for region_id in update_pending:
                if regions[region_id].update_region(polygon, score): break
            else: region_id = None

            if region_id is not None:
                update_pending.discard(region_id)
            else:
                new_polygons.append(polygon)

        new_texts = ocr(image, new_polygons)
        for polygon, text in zip(new_polygons, new_texts):
            region_id = uuid4().hex
            regions[region_id] = Region(polygon, text, region_id)

        for lost_region_id in update_pending:
            del regions[lost_region_id]

        for region in regions.values():
            region.draw(image)

    return image
