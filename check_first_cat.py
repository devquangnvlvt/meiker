import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    if item.get("type") in ("category", "stamps", "icon-set"):
        kids = item.get("children", [])
        if kids:
            print(f"Cat {item['id']} '{item.get('name')}' kids={len(kids)}")
            for k in kids[:3]:
                print(f"  - Kid {k['id']} x={k.get('x')} y={k.get('y')}")
            break
