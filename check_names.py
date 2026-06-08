import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def find_item_and_print_children(item_list, target_id):
    for item in item_list:
        if item.get('id') == target_id:
            kids = item.get('children', [])
            for kid in kids:
                print(f"Kid {kid['id']}: name='{kid.get('name')}', type='{kid.get('type')}', vis={kid.get('visible')}")
            return True
        if find_item_and_print_children(item.get('children', []), target_id):
            return True
    return False

find_item_and_print_children(data, 1334388)
