import json
from PIL import Image

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Checking Image Dimensions and XY ---")
def check_item(item_id):
    # search in top level
    item = next((i for i in data if i['id'] == item_id), None)
    if not item:
        # search in children
        item = next((c for i in data for c in i.get('children', []) if c['id'] == item_id), None)
    
    if item and item.get('image'):
        try:
            # We saved images as id.png
            img_path = f"downloads/meiker_13396/items/{item['id']}.png"
            with Image.open(img_path) as img:
                w, h = img.size
                print(f"ID {item['id']:7} | X: {item.get('x',0):4} Y: {item.get('y',0):4} | W: {w:4} H: {h:4}")
        except Exception as e:
            print(f"Error reading {item['id']}: {e}")

# Check body and a few outfits
check_item(1334253) # Body
check_item(1334388) # Outfit 1
check_item(1334403) # Outfit 2
check_item(1335596) # Something else
check_item(1336781) # UI Background (should be 0,0)
