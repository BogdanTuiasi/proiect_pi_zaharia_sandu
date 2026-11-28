import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

IOU_THR = 0.25

# Cat % se suprapun 2 poligoane (Intersection over Union)
# Nu conteaza ordinea colturilor sau cat de mare e textul
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

# Verifica intai ca dimensiunile sa fie relativ apropiate
# (sa nu lipeasca un titlu scurt de un rand lung),
# apoi da scorul IoU daca trece de prag
def match_score(poly_a: np.ndarray, poly_b: np.ndarray) -> float:
    a = np.asarray(poly_a, dtype=np.float32).reshape(-1, 2)
    b = np.asarray(poly_b, dtype=np.float32).reshape(-1, 2)
    wa, ha = a.max(axis=0) - a.min(axis=0)
    wb, hb = b.max(axis=0) - b.min(axis=0)
    if min(wa, wb) < 0.7 * max(wa, wb, 1.0) or min(ha, hb) < 0.6 * max(ha, hb, 1.0):
        return 0.0
    iou = polygon_iou(poly_a, poly_b)
    return iou if iou >= IOU_THR else 0.0

# Hungarian matching.
# Returneaza o lista de perechi de indecsi pentru match-urile din cele 2 liste,
# O lista de indecsi pentru poligoanele fara pereche din prima lista
# Si similar o alta lista de indecsi pentru cele din a doua lista
def match_polygons(
    polys_a: list[np.ndarray],
    polys_b: list[np.ndarray],
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    # Nu putem face niciun matching, punem toti indecsi ca fara pereche.
    # range(len(...)) transforma lista initiala intr-o lista de indecsi.
    if not polys_a or not polys_b:
        return [], list(range(len(polys_a))), list(range(len(polys_b)))

    score_matrix = np.zeros((len(polys_a), len(polys_b)), dtype=np.float32)
    for r, poly_a in enumerate(polys_a):
        for c, poly_b in enumerate(polys_b):
            score_matrix[r, c] = match_score(poly_a, poly_b)

    row_ind, col_ind = linear_sum_assignment(-score_matrix)
    matched: list[tuple[int, int]] = []
    matched_a: set[int] = set()
    matched_b: set[int] = set()

    for r, c in zip(row_ind, col_ind):
        if score_matrix[r, c] <= 0.0:
            continue
        matched.append((int(r), int(c)))
        matched_a.add(int(r))
        matched_b.add(int(c))

    unmatched_a = [r for r in range(len(polys_a)) if r not in matched_a]
    unmatched_b = [c for c in range(len(polys_b)) if c not in matched_b]
    return matched, unmatched_a, unmatched_b
