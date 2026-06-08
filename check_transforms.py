import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Transforms Check ---")
for item in data:
    if item.get("type") == "category":
        kids = item.get("children", [])
        if len(kids) > 5:
            for k in kids[:2]:
                print(f"ID: {k['id']} | Transform: {k.get('transform', [])} | XY: {k.get('x')}, {k.get('y')}")
            break
