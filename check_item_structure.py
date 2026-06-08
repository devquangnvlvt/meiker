import json
import sys

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def find_item_and_print_children(item_list, target_id):
    for item in item_list:
        if item.get('id') == target_id:
            print(f"Found {target_id}: '{item.get('name')}', type: '{item.get('type')}', image: '{item.get('image', '') != ''}'")
            kids = item.get('children', [])
            print(f"  Children: {len(kids)}")
            for kid in kids:
                print(f"    - ID: {kid.get('id')}, type: '{kid.get('type')}', image: '{kid.get('image', '') != ''}', x={kid.get('x')}, y={kid.get('y')}")
            return True
        if find_item_and_print_children(item.get('children', []), target_id):
            return True
    return False

print("--- Checking Outfit Option 1334388 ---")
find_item_and_print_children(data, 1334388)
