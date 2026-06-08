import os
import json
import shutil

import sys

game_id = sys.argv[1] if len(sys.argv) > 1 else '13396'
src_dir = rf"d:\laragon\www\meiker\downloads\meiker_{game_id}"
dest_dir = rf"d:\laragon\www\meiker\downloads\meiker_{game_id}_engine"

def get_hash(url):
    if not url: return ""
    return url.split('/')[-1].split('?')[0]

def clean_filename(name):
    if not name: return ""
    import re
    s = str(name).replace('#', '')
    return re.sub(r'[^\w\-\.\ ]', '_', s)

def build_sequence(nodes, seq=None):
    if seq is None: seq = []
    if not isinstance(nodes, list): return seq
    for node in nodes:
        if node.get('type') == 'image' and node.get('image'):
            seq.append({
                'hash': get_hash(node['image']),
                'url': node['image'],
                'x': node.get('x', 0),
                'y': node.get('y', 0)
            })
        if 'children' in node:
            build_sequence(node['children'], seq)
    return seq

def main():
    print("Loading data...")
    ui_path = os.path.join(src_dir, "ui_config.json")
    with open(ui_path, 'r', encoding='utf-8') as f:
        ui_config = json.load(f)

    raw_path = os.path.join(src_dir, "raw_data.json")
    with open(raw_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print("Building Z-Index sequence...")
    seq = build_sequence(raw_data)
    z_map = {}
    for i, item in enumerate(seq):
        z_map[item['hash']] = i + 1 # 1-based Z-index

    print("Structuring by Category...")
    # Group categories to assign X (1, 2, 3...)
    cat_order = []
    for asset in ui_config['assets']:
        c = asset.get('category', 'misc')
        if c not in cat_order:
            cat_order.append(c)

    os.makedirs(dest_dir, exist_ok=True)

    # We want folders: {X}-{Y}
    # But files inside the same category might have DIFFERENT Y (z-indexes).
    # To keep the category grouping intuitive, we group all assets of a category into a SINGLE folder 
    # named X-{Avg_Y} or just {X}-{CatName}, but the user specifically asked for X-Y.
    # Since one category can have multiple Z-indexes, we will create a folder X-Y for EVERY Z-index layer used by that category!
    # e.g., if Hair uses Z=10 and Z=50, we get 3-10 and 3-50.
    
    # Wait, if we use X-Y for EVERY image, that's too many folders!
    # Let's group by Category (X) and Z-index (Y).
    
    category_groups = {}
    
    for asset in ui_config['assets']:
        cat = asset.get('category', 'misc')
        x_val = cat_order.index(cat) + 1
        
        file_hash = get_hash(asset['url'])
        y_val = z_map.get(file_hash, 999)
        
        col = clean_filename(asset.get('color', ''))
        local_rel = os.path.join(clean_filename(cat), col, asset['filename']) if col else os.path.join(clean_filename(cat), asset['filename'])
        src_file = os.path.join(src_dir, local_rel)
        
        folder_key = x_val
        if folder_key not in category_groups:
            category_groups[folder_key] = {
                'x': x_val,
                'y_list': [],
                'assets': [],
                'cat_name': cat
            }
            
        if y_val != 999:
            category_groups[folder_key]['y_list'].append(y_val)
            
        if os.path.exists(src_file):
            category_groups[folder_key]['assets'].append({
                'src': src_file,
                'color': col
            })

    for folder_key, group in category_groups.items():
        # Determine Y (Z-index) for this entire category
        # Use the minimum valid Z-index as the representative layer for the whole folder
        valid_ys = group['y_list']
        y_val = min(valid_ys) if valid_ys else 999
        
        out_folder = os.path.join(dest_dir, f"{group['x']}-{y_val}")
        os.makedirs(out_folder, exist_ok=True)
        
        color_counters = {}
        created_thumbs = set()
        nav_created = False
        
        for asset in group['assets']:
            src_file = asset['src']
            col = asset['color']
            
            color_counters[col] = color_counters.get(col, 0) + 1
            item_idx = color_counters[col]
            
            ext = os.path.splitext(src_file)[1]
            
            if col:
                col_folder = os.path.join(out_folder, col)
                os.makedirs(col_folder, exist_ok=True)
                dest_file = os.path.join(col_folder, f"{item_idx}{ext}")
            else:
                dest_file = os.path.join(out_folder, f"{item_idx}{ext}")
                
            shutil.copy2(src_file, dest_file)
            
            # Simple nav.png - just use the very first item's image
            nav_path = os.path.join(out_folder, "nav.png")
            if not nav_created:
                shutil.copy2(src_file, nav_path)
                nav_created = True
                
            thumb_path = os.path.join(out_folder, f"thumb_{item_idx}{ext}")
            if item_idx not in created_thumbs:
                shutil.copy2(src_file, thumb_path)
                created_thumbs.add(item_idx)

    print(f"Export complete. Check {dest_dir}")

if __name__ == '__main__':
    main()
