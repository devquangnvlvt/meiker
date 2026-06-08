"""
embed_layers.py  -  Nhung moi anh layer vao canvas 600x800 dung toa do x/y
Ket qua: moi file PNG goc duoc thay bang PNG moi kich thuoc canvas_w x canvas_h,
         anh goc nam dung vi tri (x, y), phan con lai trong suot.

Dung:
  python embed_layers.py 14745
"""

import os, sys, json
from PIL import Image

def embed_all(game_id):
    base   = os.path.join('downloads', f'meiker_{game_id}')
    mpath  = os.path.join(base, 'manifest.json')

    if not os.path.exists(mpath):
        print(f'[ERROR] Khong tim thay {mpath}')
        sys.exit(1)

    with open(mpath, encoding='utf-8') as f:
        manifest = json.load(f)

    cw = manifest.get('canvas_width',  600)
    ch = manifest.get('canvas_height', 800)
    print(f'[+] Game: {manifest["name"]}  |  Canvas: {cw}x{ch}')

    total = ok = skip = err = 0

    for cat in manifest['categories']:
        for opt in cat['options']:
            for layer in opt['layers']:
                lpath = os.path.join(base, layer['local_path'])
                x     = layer['x']
                y     = layer['y']

                if not os.path.exists(lpath):
                    print(f'[SKIP] khong co file: {lpath}')
                    skip += 1
                    continue

                try:
                    src = Image.open(lpath).convert('RGBA')
                    sw, sh = src.size

                    # Neu anh da dung kich thuoc canvas -> bo qua
                    if sw == cw and sh == ch:
                        skip += 1
                        total += 1
                        continue

                    # Kiem tra tran vien (canh bao nhung van xu ly)
                    if x + sw > cw or y + sh > ch or x < 0 or y < 0:
                        print(f'[WARN] tran vien: {layer["local_path"]}  '
                              f'src={sw}x{sh} @ ({x},{y})  canvas={cw}x{ch}')

                    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
                    canvas.paste(src, (x, y))
                    canvas.save(lpath, 'PNG')
                    ok += 1

                except Exception as e:
                    print(f'[ERROR] {lpath}: {e}')
                    err += 1

                total += 1
                if total % 100 == 0:
                    print(f'  {total} anh... ok={ok} skip={skip} err={err}')

    print(f'\n[+] Hoan thanh: {total} anh  |  xu ly={ok}  bo qua={skip}  loi={err}')
    print(f'[+] Gio moi layer la {cw}x{ch} px, nam dung toa do x/y.')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Dung: python embed_layers.py <game_id>')
        print('Vi du: python embed_layers.py 14745')
        sys.exit(1)
    embed_all(sys.argv[1].strip())
