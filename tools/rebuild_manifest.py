"""img/manifest.js を { 課題: {src, segs} } の形で作りなおす（画像は変えない）。
使い方: python tools/rebuild_manifest.py
"""
import json, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from segment import find_segments

mp = 'img/manifest.js'
txt = open(mp, encoding='utf-8').read()
m = json.loads(re.search(r'window\.GEN_IMAGES = (\{.*?\});', txt, re.S).group(1))
out, bad = {}, []
for word, v in m.items():
    src = v['src'] if isinstance(v, dict) else v
    segs = find_segments(src, len(word))
    if segs is None:
        bad.append(word)
    out[word] = {'src': src, 'segs': segs}
body = ',\n'.join(f'  {json.dumps(w, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}' for w, v in out.items())
open(mp, 'w', encoding='utf-8').write('// 課題文字 → 筆書き画像（Flow生成）。微小な独立した墨を除いた文字範囲。\n// segs は1文字ごとの範囲 [y0, y1, x0, x1]（px）。null のときは画像全体を使う\nwindow.GEN_IMAGES = {\n' + body + '\n};\n')
print(len(out), 'entries; segs失敗:', bad)
