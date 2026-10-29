"""gen_raw/b{バッチ}_{連番}_a.jpg を、課題リスト(tools/words.txt)の順番どおりに img/wNN.webp にして manifest.js を更新する。
使い方: python tools/build_images.py バッチ番号 先頭の課題番号(1始まり)  または  課題番号のカンマ区切り
  例: python tools/build_images.py 1 1   # バッチ1の1枚目 = 課題1番
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from process_image import process

batch = int(sys.argv[1])
# 第2引数が "12,13,14,..." のように , を含むときは、送信順に対応する課題番号の一覧
idx_arg = sys.argv[2]
idx_list = [int(x) for x in idx_arg.split(',')] if ',' in idx_arg else None
start = int(idx_arg) if idx_list is None else 0
words = open('tools/words.txt', encoding='utf-8').read().split('\n')
mp = 'img/manifest.js'
txt = open(mp, encoding='utf-8').read()
m = json.loads(re.search(r'window\.GEN_IMAGES = (\{.*?\});', txt, re.S).group(1))
k = 1
while os.path.exists(f'gen_raw/b{batch}_{k:02d}_a.jpg'):
    idx = idx_list[k - 1] if idx_list else start + k - 1
    word = words[idx - 1]
    out = f'img/w{idx:02d}.webp'
    process(f'gen_raw/b{batch}_{k:02d}_a.jpg', out)
    m[word] = out
    k += 1
body = ',\n'.join(f'  {json.dumps(w, ensure_ascii=False)}: {json.dumps(p)}' for w, p in m.items())
open(mp, 'w', encoding='utf-8').write('// 課題文字 → 筆書き画像（Flow で生成し、教員が確認したものだけを入れる）\nwindow.GEN_IMAGES = {\n' + body + '\n};\n')
print(len(m), 'entries')

os.system('python tools/rebuild_manifest.py')
