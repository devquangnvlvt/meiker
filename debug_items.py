import json, os

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Build flat map
flat = {}
def collect(items):
    for it in items:
        flat[it['id']] = it
        collect(it.get('children', []))
collect(data)

# For each category, check children x,y range
print("=== CATEGORY CHILDREN COORDINATE ANALYSIS ===\n")
for item in data:
    itype = item.get('type','?')
    if itype not in ('category','stamps','icon-set'):
        continue
    kids = item.get('children', [])
    if not kids:
        continue
    xs = [c.get('x',0) for c in kids]
    ys = [c.get('y',0) for c in kids]
    tags = str(item.get('tags',[]))[:50]
    vis_kids = [c for c in kids if c.get('visible')]
    print(f"id={item['id']} type={itype} x={item.get('x')} y={item.get('y')} | kids={len(kids)} vis={len(vis_kids)} | child_x=[{min(xs)}-{max(xs)}] child_y=[{min(ys)}-{max(ys)}] | tags={tags}")
