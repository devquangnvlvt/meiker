import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Category Hierarchy ---")
for it in data:
    parent_id = it.get('parent_id')
    print(f"ID {it['id']:7} | Type: {it.get('type'):12} | Name: {it.get('name'):15} | Parent: {parent_id}")
    kids = it.get('children', [])
    if kids:
        for k in kids[:3]:
            print(f"  - Kid {k['id']:7} | Type: {k.get('type'):12} | Name: {k.get('name'):15}")
