"""筆書き画像（透明背景 WebP）を、1文字ずつの範囲 [y0, y1, x0, x1]（画像のpx）に分ける。
アプリで、文字ごとに間隔を広げて縦いっぱいに並べ、各文字を中心線にそろえるために使う。
文字数は課題文字の長さと一致させる（ちがうときは None を返し、アプリは画像全体をそのまま使う）。

方法:
 1. 墨のない行（すきま）で、墨のかたまり(run)に分ける。
 2. 切り位置の候補 = かたまりの間のすきま ＋ 長いかたまり（文字が上下で触れている）の中の、墨がいちばん少ない行。
 3. 「全体を文字数で等分した位置」に近く、かつ広いすきまほど有利になるように、n-1 個の切り位置を選ぶ
    （「元」の上の横画と本体のあいだ、のような1文字の中の小さなすきまで切らないため）。
 4. 各文字の左右の墨の端(x0, x1)を求める。
"""
from PIL import Image
import re


def character_ink_bbox(ink):
    """離れた微小な墨を除いて字の外接枠を求める。点・濁点などは残す。

    二値画像を横方向の連続区間に分け、上下（斜めを含む）に接する区間を
    連結する。最大の墨の塊の0.3%未満の、ごく小さな独立成分だけを無視。
    元の画像は変更せず、文字の実際の画の端まで含む座標を返す。
    """
    w, h = ink.size
    data = ink.tobytes()
    parent, boxes, areas = [], [], []

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    previous = []
    for y in range(h):
        current = []
        for match in re.finditer(b"\xff+", data[y * w:(y + 1) * w]):
            a, b = match.span()
            hits = {root(i) for pa, pb, i in previous if pa <= b and pb >= a}
            if hits:
                i = min(hits)
                for other in hits - {i}:
                    parent[other] = i
                    areas[i] += areas[other]
                    box, old = boxes[i], boxes[other]
                    boxes[i] = [min(box[0], old[0]), min(box[1], old[1]),
                                max(box[2], old[2]), max(box[3], old[3])]
                box = boxes[i]
                boxes[i] = [min(box[0], a), min(box[1], y), max(box[2], b), y + 1]
                areas[i] += b - a
            else:
                i = len(parent)
                parent.append(i)
                boxes.append([a, y, b, y + 1])
                areas.append(b - a)
            current.append((a, b, i))
        previous = current
    components = [i for i in range(len(parent)) if root(i) == i]
    if not components:
        return None
    threshold = max(4, max(areas[i] for i in components) * 0.003)
    kept = [boxes[i] for i in components if areas[i] >= threshold]
    if not kept:
        return tuple(boxes[max(components, key=lambda i: areas[i])])
    return (min(b[0] for b in kept), min(b[1] for b in kept),
            max(b[2] for b in kept), max(b[3] for b in kept))


def find_segments(path, n):
    im = Image.open(path)
    alpha = im.getchannel("A")
    w, h = alpha.size
    ink = alpha.point(lambda v: 255 if v > 128 else 0)
    prof = list(ink.resize((1, h), Image.BOX).getdata())  # 各行の墨の量（0〜255）
    runs, start = [], None
    for y, v in enumerate(prof):
        if v > 2 and start is None:
            start = y
        elif v <= 2 and start is not None:
            runs.append([start, y]); start = None
    if start is not None:
        runs.append([start, h])
    runs = [r for r in runs if r[1] - r[0] > h * 0.01]  # ごく小さいゴミは無視
    if not runs:
        return None
    top, bottom = runs[0][0], runs[-1][1]
    pitch = (bottom - top) / n

    def finish(cuts):
        bounds = [0] + sorted(cuts) + [h]
        segs = []
        for a, b in zip(bounds[:-1], bounds[1:]):
            rows = [y for y in range(int(a), int(b)) if prof[y] > 2]
            if not rows:
                return None
            y0, y1 = rows[0], rows[-1] + 1
            box = character_ink_bbox(ink.crop((0, y0, w, y1)))
            if not box:
                return None
            segs.append([y0 + box[1], y0 + box[3], box[0], box[2]])
        return segs

    if n == 1:
        return finish([])

    # 切り位置の候補: (位置, すきまの広さ)
    cands = [((runs[i][1] + runs[i + 1][0]) / 2, runs[i + 1][0] - runs[i][1]) for i in range(len(runs) - 1)]
    for y0, y1 in runs:  # 長いかたまりは、中で切る候補も作る
        m = round((y1 - y0) / pitch)
        if m >= 2:
            for j in range(1, m):
                t = y0 + (y1 - y0) * j / m
                lo, hi = int(t - pitch * 0.25), int(t + pitch * 0.25)
                y = min(range(max(y0 + 3, lo), min(y1 - 3, hi)), key=lambda q: sum(prof[q - 3:q + 4]))
                if sum(prof[y - 3:y + 4]) / 7 <= 60:  # 切り口の墨が多い（ちぎれてしまう）ものは除く
                    cands.append((y, 0))

    cuts, free = [], list(cands)
    for k in range(1, n):
        target = top + pitch * k
        if not free:
            return None
        best = min(free, key=lambda c: abs(c[0] - target) / pitch - 0.5 * min(c[1], 100) / 100)
        free.remove(best)
        cuts.append(best[0])
    return finish(cuts)
