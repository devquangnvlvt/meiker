import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Looking for Hair and Alignment ---")
for idx, item in enumerate(data):
    name = str(item.get('name', '')).lower()
    tags = str(item.get('tags', [])).lower()
    if 'hair' in name or 'hair' in tags:
        print(f"Index {idx:4} | ID {item['id']:7} | X: {item.get('x',0):4} Y: {item.get('y',0):4} | Name: {item.get('name')}")
        kids = item.get('children', [])
        if kids:
            for k in kids[:2]:
                print(f"  - Kid {k['id']:7} | X: {k.get('x',0):4} Y: {k.get('y',0):4} | Name: {k.get('name')}")
                if k.get('children'):
                    for gc in k['children'][:1]:
                        print(f"    - G-Kid {gc['id']:7} | X: {gc.get('x',0):4} Y: {gc.get('y',0):4} | Name: {gc.get('name')}")
