import json

with open('downloads/meiker_18554/raw_data.json', encoding='utf-8') as f:
    raw = json.load(f)

def get_leaves(nodes, out=None):
    if out is None: out = []
    for n in nodes:
        if n.get('image'): out.append(n['id'])
        if n.get('children'): get_leaves(n['children'], out)
    return out

flat_z = get_leaves(raw)

with open('downloads/meiker_18554/manifest.json', encoding='utf-8') as f:
    m = json.load(f)

for cat in m['categories']:
    cat_z_indices = []
    for opt in cat['options']:
        for l in opt['layers']:
            try:
                z = flat_z.index(l['id'])
                cat_z_indices.append(z)
            except: pass
    if cat_z_indices:
        print(f"Category {cat['folder']} (fixed={cat['is_fixed']}): min Z = {min(cat_z_indices)}, max Z = {max(cat_z_indices)}")
