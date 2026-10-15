"""Remove the UI chips/labels baked into the original floor-plan render and
enhance it, producing floorplan.jpg for the dashboard.

usage: python tools/clean_floorplan.py original.jpg floorplan.jpg
needs: pip install opencv-python-headless pillow numpy
"""
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# (x1, y1, x2, y2) in original 1365x768 pixel coordinates
BOXES = [
    # living room / entrance / store
    (252, 201, 321, 297), (604, 138, 639, 184), (606, 200, 636, 214), (532, 251, 569, 298),
    (435, 206, 474, 220), (310, 414, 402, 439), (209, 467, 270, 501), (189, 546, 234, 587),
    (200, 616, 259, 651), (282, 614, 341, 629),
    # kitchen / dining
    (537, 419, 580, 469), (660, 362, 707, 422), (654, 436, 712, 451), (712, 552, 754, 569),
    (534, 584, 570, 621), (597, 586, 635, 601), (570, 622, 604, 649), (570, 655, 604, 686),
    (655, 617, 689, 655), (726, 620, 764, 657), (763, 628, 823, 649), (729, 666, 760, 699),
    (492, 427, 526, 459), (492, 586, 526, 616),
    # corridor / kids room
    (815, 112, 849, 146), (970, 95, 1001, 126), (1012, 95, 1044, 126), (910, 144, 964, 159),
    (902, 185, 974, 219), (1102, 111, 1160, 150), (1161, 111, 1219, 150),
    (1155, 167, 1178, 209), (1179, 167, 1354, 209), (839, 300, 881, 317),
    # master bathroom
    (965, 275, 997, 306), (1010, 267, 1044, 299), (1064, 265, 1099, 301), (1010, 300, 1096, 317),
    (956, 314, 992, 350), (944, 350, 1005, 385), (1164, 314, 1185, 350), (1186, 314, 1264, 350),
    # master bedroom
    (1164, 411, 1203, 472), (1204, 411, 1305, 472), (992, 489, 1109, 540), (1004, 544, 1084, 557), (1145, 521, 1181, 559),
    (1012, 574, 1086, 614), (1187, 579, 1217, 621), (1218, 579, 1306, 621), (1100, 626, 1134, 676), (1220, 624, 1271, 674),
]

# regions whose labels sit on busy texture (rugs, sofas, beds): these are
# replaced with a matching patch copied from nearby; everything else gets a
# smooth membrane fill
GLOW = 6
PATCH = [(150, 190, 480, 720), (880, 30, 1150, 230)]

def main(src, dst):
    img = cv2.imread(src)
    h, w = img.shape[:2]
    # 1) left status panels + weather card sit on the plain backdrop: fill by gradient
    for y in range(0, 474):
        a = img[y, 1].astype(float)
        xb = 153 if y < 215 else 149
        b = img[y, xb].astype(float)
        if b.sum() < 300:
            b = a
        t = np.linspace(0, 1, xb - 1)[:, None]
        img[y, 1:xb] = (a * (1 - t) + b * t).astype(np.uint8)
    for x in range(1174, w):
        a, b = img[0, x].astype(float), img[104, x].astype(float)
        t = np.linspace(0, 1, 104)[:, None]
        img[0:104, x] = (a * (1 - t) + b * t).astype(np.uint8)
    img[0:480, 0:150] = cv2.GaussianBlur(img[0:486, 0:156], (0, 0), 8)[0:480, 0:150]
    img[0:108, 1170:w] = cv2.GaussianBlur(img[0:114, 1164:w], (0, 0), 6)[0:108, 6:]

    # 2) replace every baked-in chip / garbled label with a nearby patch of real
    #    texture (best match of the surrounding ring), Poisson-blended in.
    pad, ring = 3, 6
    rects = [[x1 - pad, y1 - pad, x2 + pad, y2 + pad] for x1, y1, x2, y2 in BOXES]
    merged = True
    while merged:  # merge overlapping rectangles
        merged = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i], rects[j]
                if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                    rects[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    rects.pop(j)
                    merged = True
                    break
            if merged:
                break
    bad = np.zeros((h, w), np.uint8)
    for x1, y1, x2, y2 in rects:
        bad[max(y1, 0):y2 + 1, max(x1, 0):x2 + 1] = 1
    integral = cv2.integral(bad)
    def clean(x1, y1, x2, y2):
        if x1 < 0 or y1 < 0 or x2 >= w or y2 >= h:
            return False
        return integral[y2 + 1, x2 + 1] - integral[y1, x2 + 1] - integral[y2 + 1, x1] + integral[y1, x1] == 0

    def smooth_fill(x1, y1, x2, y2, backdrop=False):
        # membrane fill: Poisson-clone a flat patch, i.e. the smoothest surface
        # that matches the surrounding pixels exactly, then add film grain.
        nonlocal img
        x1, y1, x2, y2 = max(x1, 2), max(y1, 2), min(x2, w - 3), min(y2, h - 3)
        src = np.full((y2 - y1 + 5, x2 - x1 + 5, 3), 128, np.uint8)
        m = np.zeros(src.shape[:2], np.uint8)
        m[2:-2, 2:-2] = 255
        img = cv2.seamlessClone(src, img, m, ((x1 + x2) // 2 + 0, (y1 + y2) // 2 + 0), cv2.NORMAL_CLONE)
        reg = img[y1:y2 + 1, x1:x2 + 1].astype(np.float32)
        reg += np.random.default_rng(x1 * 7 + y1).normal(0, 2.2, reg.shape)
        img[y1:y2 + 1, x1:x2 + 1] = np.clip(reg, 0, 255).astype(np.uint8)

    in_patch = lambda x1, y1, x2, y2: any(b[0] <= x1 and x2 <= b[2] and b[1] <= y1 and y2 <= b[3] for b in PATCH)
    f = img.astype(np.float32)
    for x1, y1, x2, y2 in rects:
        x1, y1, x2, y2 = max(x1, ring), max(y1, ring), min(x2, w - ring - 1), min(y2, h - ring - 1)
        X1, Y1, X2, Y2 = x1 - ring, y1 - ring, x2 + ring, y2 + ring
        tgt = f[Y1:Y2 + 1, X1:X2 + 1]
        rmask = np.ones(tgt.shape[:2], np.float32)
        rmask[ring:-ring, ring:-ring] = 0
        rmask *= 1 - bad[Y1:Y2 + 1, X1:X2 + 1]
        ring_px = tgt[rmask > 0]
        ring_mean, ring_std = ring_px.mean(0), ring_px.std(0)
        if not in_patch(x1, y1, x2, y2):
            smooth_fill(x1 - GLOW, y1 - GLOW, x2 + GLOW, y2 + GLOW)  # also swallow the chip's glow
            f = img.astype(np.float32)
            continue
        bw, bh = X2 - X1 + 1, Y2 - Y1 + 1
        best, best_cost = None, 1e18
        span = int(max(bw, bh) * 1.6)
        for dy in range(-span, span + 1, 2):
            for dx in range(-span, span + 1, 2):
                if abs(dx) < bw - ring and abs(dy) < bh - ring:
                    continue
                if not clean(X1 + dx, Y1 + dy, X2 + dx, Y2 + dy):
                    continue
                cand = f[Y1 + dy:Y2 + dy + 1, X1 + dx:X2 + dx + 1]
                inner = cand[ring:-ring, ring:-ring].reshape(-1, 3)
                cost = ((((cand - tgt) ** 2).sum(2) * rmask).sum()
                        + ((inner.mean(0) - ring_mean) ** 2).sum() * inner.shape[0] * 2
                        + ((inner.std(0) - ring_std) ** 2).sum() * inner.shape[0] * 2
                        + 40 * (dx * dx + dy * dy) ** .5 * rmask.sum() / 50)
                if cost < best_cost:
                    best, best_cost = (dx, dy), cost
        if best is None:
            smooth_fill(x1, y1, x2, y2, False)
            f = img.astype(np.float32)
            continue
        dx, dy = best
        src = img[Y1 + dy:Y2 + dy + 1, X1 + dx:X2 + dx + 1].copy()
        m = np.zeros(src.shape[:2], np.uint8)
        m[2:-2, 2:-2] = 255
        center = ((X1 + X2 + 1) // 2, (Y1 + Y2 + 1) // 2)
        img = cv2.seamlessClone(src, img, m, center, cv2.NORMAL_CLONE)
        f = img.astype(np.float32)

    # 3) upscale 2x and enhance
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pil = pil.resize((w * 2, h * 2), Image.LANCZOS)
    pil = pil.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    pil = ImageEnhance.Contrast(pil).enhance(1.06)
    pil = ImageEnhance.Color(pil).enhance(1.08)
    pil.save(dst, quality=86, optimize=True, progressive=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
