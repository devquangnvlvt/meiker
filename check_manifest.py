import json
with open('downloads/meiker_18554/manifest.json', encoding='utf-8') as f:
    m = json.load(f)
print('Categories:', len(m['categories']))
print('Static layers:', len(m['static']))
print()
for cat in m['categories']:
    folder = cat['folder']
    label  = cat['label']
    opts   = len(cat['options'])
    layers = sum(len(o['layers']) for o in cat['options'])
    opt    = cat['is_optional']
    print(f'  {folder:20} label={label:12} opts={opts} layers={layers} optional={opt}')
print()
if m['static']:
    print('Sample static:', m['static'][0])
else:
    print('No static layers')
