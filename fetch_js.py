import urllib.request
import re

url = "https://meiker.io/play/13396/online.html"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req).read().decode('utf-8')

scripts = re.findall(r'<script\s+src=["\']([^"\']+\.js)["\']', html)
print("JS Files:", scripts)

for js in scripts:
    if 'bundle' in js or 'meiker' in js or 'vendors' in js:
        full_url = js if js.startswith('http') else 'https://meiker.io' + ('/' + js if not js.startswith('/') else js)
        print("Checking", full_url)
        try:
            req2 = urllib.request.Request(full_url, headers=headers)
            js_code = urllib.request.urlopen(req2).read().decode('utf-8')
            # Look for anchor settings
            if 'anchor.set' in js_code:
                print("FOUND Anchor.set in", js)
                idx = js_code.find('anchor.set')
                print(js_code[max(0, idx-50):min(len(js_code), idx+100)])
        except Exception as e:
            print("Error loading", js, e)
