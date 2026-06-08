import json

with open('downloads/13396_Monster girl maker/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find items that might be structured as Item -> Colors -> Layers or Item -> Layers
for item in data:
    # Look for items with many children, where children also have children?
    if 'children' in item and len(item['children']) > 0:
        has_grandkids = any('children' in c and len(c['children']) > 0 for c in item['children'])
        if has_grandkids:
            print(f"Item {item.get('name')} (id {item.get('id')}) has grandkids!")
            print(f"  First child {item['children'][0].get('name')} (tags {item['children'][0].get('tags')}):")
            print(f"    Grandkids count: {len(item['children'][0].get('children'))}")
            break

# Are there any items with 'layers' list?
layers_items = [i for i in data if 'layers' in i]
print(f"Items with 'layers' keyword: {len(layers_items)}")

# Are there any items with 'options' list?
options_items = [i for i in data if 'options' in i]
print(f"Items with 'options' keyword: {len(options_items)}")

# Are there any items with 'images' list?
images_items = [i for i in data if 'images' in i]
print(f"Items with 'images' keyword: {len(images_items)}")
