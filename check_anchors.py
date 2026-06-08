import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Checking Skin and Outfit Coords ---")
for item in data:
    if item.get("type") == "icon-set" and "skins" in item.get("tags", []):
        print(f"SKINS Cat {item['id']}")
        for k in item.get('children', [])[:2]:
            print(f"  - Kid {k['id']}: x={k.get('x')}, y={k.get('y')}")
        break

print("\n--- Any anchors? ---")
found_anchors = 0
for item in data:
    for k in item.keys():
        if "anchor" in k or "pivot" in k or "offset" in k:
            print("Found property:", k, "in item", item['id'])
            found_anchors += 1
if found_anchors == 0:
    print("No anchor/pivot/offset properties found in top level items.")
