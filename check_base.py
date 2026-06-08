import json
from PIL import Image
import os

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Looking for Base Images (w > 200, h > 200) ---")
for item in data[:50]:
    if item.get('type') in ('image', 'color-picker', 'icon-set'):
        iid = item.get('id')
        img_url = item.get('image')
        if img_url:
            path = f"downloads/meiker_13396/items/{iid}.png"
            if os.path.exists(path):
                with Image.open(path) as img:
                    w, h = img.size
                    if w > 200 and h > 200:
                        print(f"Base candidate: ID={iid} X={item.get('x')} Y={item.get('y')} W={w} H={h}")
        else:
            for k in item.get('children', [])[:2]:
                kid = k.get('id')
                path = f"downloads/meiker_13396/items/{kid}.png"
                if os.path.exists(path):
                    with Image.open(path) as img:
                        w, h = img.size
                        if w > 200 and h > 200:
                            print(f"Base Child candidate: Parent={iid} Child={kid} X={k.get('x')} Y={k.get('y')} W={w} H={h}")
