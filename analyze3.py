import json

with open('downloads/13396_Monster girl maker/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    if item.get('id') == 1334387:
        print("Root Item:", item.get('name'), item.get('tags'))
        print("Child 0:")
        if item.get('children'):
            child = item['children'][0]
            print(json.dumps({k: v for k, v in child.items() if k != 'children'}, indent=2))
            if child.get('children'):
                print("Grandchild 0:")
                gc = child['children'][0]
                print(json.dumps(gc, indent=2))
        break
