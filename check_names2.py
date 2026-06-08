import json
with open('downloads/meiker_18554/raw_data.json', encoding='utf-8') as f:
    data = json.load(f)
for item in data:
    if item.get('type') in ('category', 'stamps', 'icon-set'):
        print(f"=== Category: {item['name']} (type={item['type']}) ===")
        for ch in item.get('children', [])[:4]:
            cname = ch.get('name','')
            ctags = str(ch.get('tags',[]))[:100]
            ctype = ch.get('type','')
            print(f"  child type={ctype} name={cname} tags={ctags}")
            # Peek into grandchildren
            for gch in ch.get('children', [])[:2]:
                print(f"    grandchild type={gch.get('type')} name={gch.get('name')} tags={str(gch.get('tags',[]))[:60]}")
        print()
