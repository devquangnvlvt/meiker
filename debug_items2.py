import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- OUTFIT / CATEGORIES CHILDREN ---")
for item in data:
    if item.get("type") == "category":
        kids = item.get("children", [])
        if len(kids) > 5:
            print(f"Cat {item['id']} ({item.get('name')}): {len(kids)} kids")
            for k in kids[:3]:
                print(f"  - Kid {k['id']}: x={k.get('x')}, y={k.get('y')} img={bool(k.get('image'))}")
            # print only first category
            break

print("\n--- TYPES OF ITEMS AT NON-ZERO COORDS ---")
count_nz = 0
for item in data:
    if item.get("x", 0) != 0 or item.get("y", 0) != 0:
        count_nz += 1
        print(f"NZ Item {item['id']} ({item.get('name')}): type={item.get('type')}, x={item.get('x')}, y={item.get('y')}")
print(f"Total top-level items with non-zero coords: {count_nz}")
