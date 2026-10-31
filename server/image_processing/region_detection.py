from uuid import uuid4
import numpy as np
from paddleocr import TextDetection
from .ocr import ocr
from .region import Region

detector = TextDetection(
    model_name="PP-OCRv5_mobile_det",
    device="gpu",
    enable_mkldnn=False,
)

regions: dict[str, Region] = {}
update_pending: list[str] = []

# detector.paddlex_predictor.post_op.box_type = "poly"   

def proc(image: np.ndarray):
    for result in detector.predict(image):
        update_pending = regions.keys
        for polygon, score in zip(result["dt_polys"], result["dt_scores"]):
            if(score < 70): continue

            polygon = np.asarray(polygon, dtype=np.int32)
            for region_id in update_pending:
                if(regions[region_id].update_region(polygon, score)): break
            else: region_id = None

            if(region_id != None):
                update_pending.remove(region_id)
            else:
                text = ocr(image, polygon)
                region_id = uuid4().hex
                regions[region_id] = Region(polygon, text)
            
            regions[region_id].draw(image)
            
    print(regions)
    return image
