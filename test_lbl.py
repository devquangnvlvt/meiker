import json
import re

ui_path = r"d:\laragon\www\meiker\downloads\meiker_13396\ui_config.json"
with open(ui_path, 'r', encoding='utf-8') as f:
    ui_config = json.load(f)

cats_seen = set()
for asset in ui_config['assets']:
    cat = asset.get('category', 'misc')
    col = asset.get('color', '')
    lbl = asset.get('label', '')
    
    if col and cat not in cats_seen:
        cats_seen.add(cat)
        print(f"Cat: {cat}")
        
    if cat in ['skins', 'hair'] and len(cats_seen) < 5:
        print(f"  {cat} - col:{col} - lbl:{lbl} - file: {asset['filename']}")
