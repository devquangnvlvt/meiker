import json
import re

def parse_flat_items(items, parent_name="", parent_color=""):
    result = []
    if not isinstance(items, list): return result
        
    for item in items:
        tags = item.get('tags', [])
        cat_name = parent_name
        
        for prefix in ['icon-set:', 'enable-color-global:', 'color-picker:', 'enable-color-item:']:
            if prefix in str(tags):
                for t in tags:
                    if isinstance(t, str) and t.startswith(prefix):
                        cat_name = t.split(':')[1]
                        break
                        
        if not cat_name and item.get('type') == 'icon-set':
            cat_name = item.get('name', 'icon_set')
            
        if not cat_name:
            cat_name = 'misc'
            
        color_name = parent_color
        if item.get('type') == 'image-color' or item.get('name', '').startswith('#'):
            color_name = item.get('name', parent_color)
            
        if 'image' in item:
            result.append({'category': cat_name, 'color': color_name, 'url': item['image']})
            
        if 'children' in item:
            child_cat = cat_name if cat_name != 'misc' else item.get('name', '')
            result.extend(parse_flat_items(item['children'], child_cat, color_name))
            
    return result

with open('downloads/13396_Monster girl maker/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

res = parse_flat_items(data)
categories = set(c['category'] for c in res)
print("Extracted Categories:", sorted(list(categories)))
