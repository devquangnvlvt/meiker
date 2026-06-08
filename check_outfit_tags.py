import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- Checking Outfit Tags and Name ---")
for item in data:
    if item.get("id") == 1334387:
        print(f"ID 1334387:")
        print(f"  Name: {item.get('name')}")
        print(f"  Type: {item.get('type')}")
        print(f"  Tags: {item.get('tags')}")
        
        kids = item.get('children', [])
        print(f"  Kids: {len(kids)}")
        if kids:
            print(f"  First Kid:")
            print(f"    Name: {kids[0].get('name')}")
            print(f"    Tags: {kids[0].get('tags')}")
            print(f"    X/Y: {kids[0].get('x')}/{kids[0].get('y')}")
        break
