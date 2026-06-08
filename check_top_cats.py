import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Top Level Categories ---")
cats = [i for i in data if i.get('parent_id') is None and i.get('type') in ('category', 'stamps', 'icon-set')]
for idx, c in enumerate(cats):
    kids = c.get('children', [])
    print(f"Index {idx}: ID {c['id']} '{c.get('name')}' type={c.get('type')} kids={len(kids)}")
    if kids:
        for k in kids[:2]:
            print(f"  - Kid {k['id']} type={k.get('type')} x={k.get('x')} y={k.get('y')} name={k.get('name')}")
