import json
from PIL import Image
import os

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find items that are clearly body parts
body_parts = []
def scan(items):
    for it in items:
        if it.get('image'):
            # It's an image layer
            body_parts.append(it)
        scan(it.get('children', []))

scan(data)

# Check the first few and the largest ones
print(f"Total image layers found: {len(body_parts)}")

# Sort by size (if images exist)
layer_info = []
for it in body_parts:
    path = f"downloads/meiker_13396/items/{it['id']}.png"
    if os.path.exists(path):
        with Image.open(path) as img:
            w, h = img.size
            layer_info.append({
                'id': it['id'],
                'x': it.get('x', 0),
                'y': it.get('y', 0),
                'w': w,
                'h': h,
                'name': it.get('name', ''),
                'visible': it.get('visible', False)
            })

# Sort by visibility then by area
layer_info.sort(key=lambda x: (x['visible'], x['w'] * x['h']), reverse=True)

print("\n--- Top layers by visibility and area ---")
for li in layer_info[:20]:
    print(f"ID {li['id']:7} | Visible: {str(li['visible']):5} | X: {li['x']:4} Y: {li['y']:4} | W: {li['w']:4} H: {li['h']:4} | Name: {li['name']}")
