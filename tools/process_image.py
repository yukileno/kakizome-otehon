"""Flow で生成した筆文字画像（紙の背景つき JPEG）を、アプリ用の「墨だけ・透明背景」WebP にする。
使い方: python tools/process_image.py 入力.jpg 出力.webp
"""
import sys
from PIL import Image, ImageChops, ImageFilter

UP = 3  # 印刷用に3倍へ拡大（輪郭は後でシャープにする）

def process(src, dst):
    im = Image.open(src).convert("L")
    w, h = im.size
    # 紙の明るさムラ（影・照明）を推定して割る
    small = im.resize((w // 4, h // 4), Image.BILINEAR)
    bg = small.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(12)).resize((w, h), Image.BILINEAR)
    flat = ImageChops.invert(ImageChops.subtract(bg, im, scale=0.94))  # 255 - (紙 - 画素) = 紙が白に揃う
    big = flat.resize((w * UP, h * UP), Image.LANCZOS)
    lo, hi = 95, 185  # これ以下は真っ黒、これ以上は紙
    lut = [int(255 * (1 - min(1, max(0, (v - lo) / (hi - lo))))) for v in range(256)]
    alpha = big.point(lut)
    # 文字の外接枠で切りぬく（紙のふちのゴミは外側10%を無視）
    mw, mh = alpha.size
    inner = alpha.crop((int(mw * .08), int(mh * .04), int(mw * .92), int(mh * .96)))
    box = inner.point(lambda v: 255 if v > 128 else 0).getbbox()
    ox, oy = int(mw * .08), int(mh * .04)
    pad = 12
    box = (max(0, ox + box[0] - pad), max(0, oy + box[1] - pad), min(mw, ox + box[2] + pad), min(mh, oy + box[3] + pad))
    alpha = alpha.crop(box)
    out = Image.new("LA", alpha.size, (0, 0))
    out.putalpha(alpha)
    out.convert("RGBA").save(dst, "WEBP", quality=80, method=6)
    print(dst, alpha.size)

if __name__ == "__main__":
    process(sys.argv[1], sys.argv[2])
