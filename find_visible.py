import json

with open('downloads/meiker_13396/raw_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find all items that are initially visible and have an image
print("--- Initially Visible Items ---")
def find_visible(items):
    for it in items:
        if it.get('visible') and it.get('image'):
            print(f"ID {it['id']:7} | X: {it.get('x',0):4} Y: {it.get('y',0):4} | Name: {it.get('name')}")
        find_visible(it.get('children', []))

find_visible(data)
