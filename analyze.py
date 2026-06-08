import json

with open('downloads/13396_Monster girl maker/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find item 1335533
for item in data:
    if item.get('name') == 'item-1335533':
        print(json.dumps({k: v for k, v in item.items() if k != 'children'}, indent=2))
        print("Children count:", len(item.get('children', [])))
        if item.get('children'):
            print("First child:")
            print(json.dumps(item['children'][0], indent=2))
        break
