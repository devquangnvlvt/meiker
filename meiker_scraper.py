"""
meiker_scraper.py  -  Tai toan bo assets tu meiker.io
Cau truc thu muc output:
  downloads/meiker_{id}/
    raw_data.json          <- du lieu goc
    ui_config.json         <- config cho creator.js (local_path)
    manifest.json          <- cau truc day du: categories, items, static layers
    cat_01/                <- category thu 1 (ten = ten game hoac so thu tu)
      item_01/             <- option thu 1 trong category nay
        1.png              <- layer thu nhat cua option nay
        2.png              <- layer thu hai (neu co palette/dynamic)
      item_02/
        1.png
        ...
    cat_02/
      ...
    static/                <- cac layer luon hien thi

Cach dung:
  python meiker_scraper.py 18554
"""

import os, sys, json, re, subprocess, concurrent.futures, time
import urllib.request, ssl
from PIL import Image

UA       = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
BASE_CDN = 'https://cdn.meiker.io/'

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def fetch_with_curl(url):
    print(f"[FETCH] {url}")
    try:
        result = subprocess.run(
            ['curl.exe', '-s', '-L', '-A', UA,
             '--connect-timeout', '10', '--max-time', '45', url],
            capture_output=True, check=True)
        return result.stdout.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                return r.read().decode('utf-8')
        except Exception as ex:
            print(f"[ERROR] fetch failed: {ex}")
            return None

def download_file(url, filepath):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 512:
        return True, "skip"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = r.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        return True, "ok"
    except Exception as e:
        return False, str(e)

def resolve_url(path):
    if not path:
        return None
    if path.startswith('http'):
        return path
    return BASE_CDN + path.lstrip('/')

def safe_name(name):
    """Tao ten folder/file an toan cho Windows."""
    if not name:
        return 'misc'
    name = str(name).strip().lstrip('#')   # bo dau # (vi du #7A7A9D -> 7A7A9D)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = re.sub(r'_+', '_', name).strip('._')
    return name or 'misc'

def is_tech_name(name):
    """Kiem tra xem ten co phai ten ky thuat (item-XXXXXXX) khong."""
    if not name:
        return True
    return bool(re.match(r'^item-\d+$', str(name).strip()))

# ─────────────────────────────────────────────────────────────────────────────
# Parse game page
# ─────────────────────────────────────────────────────────────────────────────

def extract_game_config(html, game_id):
    config = {'game_id': game_id}
    m = re.search(r'parseCustomDataUrl\s*\(\s*"([^"]+)"', html)
    if not m:
        print("[ERROR] Khong tim thay data_url.")
        return None
    config['data_url'] = m.group(1)
    nm = re.search(r'name:\s*"([^"]+)"', html)
    config['name'] = nm.group(1) if nm else f"Game_{game_id}"
    bm = re.search(r'base_url:\s*"([^"]+)"', html)
    config['base_url'] = bm.group(1) if bm else BASE_CDN
    wm = re.search(r'canvas_width["\s:]+(\d+)', html)
    hm = re.search(r'canvas_height["\s:]+(\d+)', html)
    config['canvas_width']  = int(wm.group(1)) if wm else None
    config['canvas_height'] = int(hm.group(1)) if hm else None
    return config

# ─────────────────────────────────────────────────────────────────────────────
# Thu thap tat ca image node (flat walk, giu nguyen thu tu z-index)
# ─────────────────────────────────────────────────────────────────────────────

def flat_walk_images(nodes, out=None):
    """Duyet de quy, tra ve list phang moi node co truong 'image'."""
    if out is None:
        out = []
    if not isinstance(nodes, list):
        return out
    for node in nodes:
        if isinstance(node, dict):
            if node.get('image'):
                out.append(node)
            flat_walk_images(node.get('children', []), out)
    return out

# ─────────────────────────────────────────────────────────────────────────────
# Phan tich cau truc category -> option -> layers
# ─────────────────────────────────────────────────────────────────────────────

def analyze_structure(raw_data):
    """
    Phan tich raw_data thanh:
    - manifest_cats  : danh sach category day du
    - static_layers  : cac layer luon hien thi (co z_index de biet vi tri trong stack)
    - id_to_path     : { image_node_id -> local_path tuong doi }
    - all_downloads  : [ { cdn_url, local_path } ]
    - render_order   : list thu tu render dung (bao gom ca static va category)
    """
    manifest_cats = []
    static_layers = []
    id_to_path    = {}
    all_downloads = []
    render_order  = []   # [{type:'static'|'category', ref: index trong list tuong ung}]

    def add_download(cdn_url, local_path):
        all_downloads.append({'cdn_url': cdn_url, 'local_path': local_path})
        return local_path

    cat_counter = 0

    # ── Xu ly cac TOP-LEVEL node ──────────────────────────────────────────────
    for z_idx, node in enumerate(raw_data):
        ntype = node.get('type', '')
        nname = node.get('name', '')
        tags  = node.get('tags', [])

        # ----- Static layers (image / simple-layer / image-dynamic top-level) -----
        if ntype in ('image', 'simple-layer', 'image-dynamic'):
            # Thu thap tat ca image ben trong node nay
            img_nodes = flat_walk_images([node]) if not node.get('image') else [node]
            static_idx = len(static_layers)

            layer_files = []
            for li, img_node in enumerate(img_nodes, start=1):
                cdn = resolve_url(img_node.get('image'))
                if not cdn:
                    continue
                local = f"static/s{z_idx:02d}_{li}.png"
                id_to_path[img_node['id']] = local
                add_download(cdn, local)
                layer_files.append({
                    'id':         img_node['id'],
                    'x':          img_node.get('x', 0),
                    'y':          img_node.get('y', 0),
                    'local_path': local,
                    'cdn_url':    cdn,
                })

            if layer_files:
                static_layers.append({
                    'z_index':  z_idx,
                    'type':     ntype,
                    'name':     nname,
                    'layers':   layer_files,
                })
                render_order.append({'type': 'static', 'index': static_idx})
            continue

        # ----- Category / Stamps / Icon-set -----
        if ntype in ('category', 'stamps', 'icon-set'):
            is_fixed    = 'fixed' in tags
            is_optional = 'optional' in tags or 'mixed' in tags

            cat_counter += 1
            x_val = cat_counter   # thu tu trong nav panel
            y_val = z_idx         # vi tri z that trong stack (tinh ca static)

            if is_tech_name(nname):
                cat_folder = f"{x_val}-{y_val}"
                cat_label  = f"Part {y_val}"
            else:
                cat_folder = f"{x_val}-{y_val}-{safe_name(nname)}"
                cat_label  = nname

            cat_entry = {
                'id':          node['id'],
                'type':        ntype,
                'name':        nname,
                'label':       cat_label,
                'folder':      cat_folder,
                'tags':        tags,
                'is_optional': is_optional,
                'is_fixed':    is_fixed,
                'x_nav':       x_val,
                'y_canvas':    y_val,
                'z_index':     z_idx,
                'options':     [],
            }

            children = node.get('children', [])

            # Kiem tra color-picker
            all_color_picker = children and all(
                c.get('type') == 'color-picker' for c in children
            )

            if all_color_picker:
                color_map = {}
                for style_idx, child in enumerate(children, start=1):
                    for img_node in child.get('children', []):
                        if not img_node.get('image'):
                            continue
                        color = img_node.get('name', '').lstrip('#').strip() or f'color_{style_idx}'
                        if color not in color_map:
                            color_map[color] = []
                        color_map[color].append({'style_idx': style_idx, 'img_node': img_node})

                for color, entries in color_map.items():
                    opt_folder  = f"{cat_folder}/{color}"
                    layers_info = []
                    for entry in entries:
                        style_idx = entry['style_idx']
                        img_node  = entry['img_node']
                        local     = f"{opt_folder}/{style_idx}.png"
                        cdn       = resolve_url(img_node['image'])
                        id_to_path[img_node['id']] = local
                        add_download(cdn, local)
                        layers_info.append({
                            'id': img_node['id'], 'x': img_node.get('x', 0),
                            'y': img_node.get('y', 0), 'visible': img_node.get('visible', True),
                            'local_path': local, 'cdn_url': cdn, 'style_idx': style_idx,
                        })
                    if layers_info:
                        cat_entry['options'].append({
                            'id': entries[0]['img_node']['id'], 'type': 'color-picker',
                            'name': color, 'label': color, 'folder': opt_folder,
                            'thumbnail': layers_info[0]['local_path'],
                            'layers': layers_info, 'visible': False,
                        })
            else:
                for opt_idx, child in enumerate(children, start=1):
                    ctype = child.get('type', '')
                    cname = child.get('name', '')

                    if is_tech_name(cname):
                        opt_label  = f"Option {opt_idx}"
                        opt_folder = f"{cat_folder}/item_{opt_idx:02d}"
                    else:
                        opt_label  = cname.lstrip('#')
                        opt_folder = f"{cat_folder}/{safe_name(cname)}"

                    opt_images  = flat_walk_images([child])
                    layers_info = []
                    for layer_idx, img_node in enumerate(opt_images, start=1):
                        local = f"{opt_folder}/{layer_idx}.png"
                        cdn   = resolve_url(img_node['image'])
                        id_to_path[img_node['id']] = local
                        add_download(cdn, local)
                        layers_info.append({
                            'id': img_node['id'], 'x': img_node.get('x', 0),
                            'y': img_node.get('y', 0), 'visible': img_node.get('visible', True),
                            'local_path': local, 'cdn_url': cdn,
                        })
                    if layers_info:
                        cat_entry['options'].append({
                            'id': child['id'], 'type': ctype, 'name': cname,
                            'label': opt_label, 'folder': opt_folder,
                            'thumbnail': layers_info[0]['local_path'],
                            'layers': layers_info, 'visible': child.get('visible', False),
                        })

            cat_ref = len(manifest_cats)
            manifest_cats.append(cat_entry)
            render_order.append({'type': 'category', 'index': cat_ref})
            continue

    return manifest_cats, static_layers, render_order, id_to_path, all_downloads

# ─────────────────────────────────────────────────────────────────────────────
# Embed moi layer vao canvas canvas_w x canvas_h dung toa do x/y
# ─────────────────────────────────────────────────────────────────────────────

def embed_layers(manifest_cats, static_layers, save_dir, cw, ch):
    print(f"\n[+] Dang embed layers vao canvas {cw}x{ch}...")
    total = ok = skip = err = 0

    # Gom tat ca layers can xu ly: category options + static
    all_layer_entries = []
    for cat in manifest_cats:
        for opt in cat['options']:
            for layer in opt['layers']:
                all_layer_entries.append(layer)
    for sl in static_layers:
        for layer in sl['layers']:
            all_layer_entries.append(layer)

    for layer in all_layer_entries:
        lpath = os.path.join(save_dir, layer['local_path'])
        x, y  = layer['x'], layer['y']

        if not os.path.exists(lpath):
            skip += 1; total += 1
            continue

        try:
            src = Image.open(lpath).convert('RGBA')
            sw, sh = src.size

            if sw == cw and sh == ch:
                skip += 1; total += 1
                continue

            canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            paste_x = max(x, 0)
            paste_y = max(y, 0)
            crop_x  = paste_x - x
            crop_y  = paste_y - y
            crop_w  = min(sw - crop_x, cw - paste_x)
            crop_h  = min(sh - crop_y, ch - paste_y)
            if crop_w > 0 and crop_h > 0:
                region = src.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
                canvas.paste(region, (paste_x, paste_y))
            canvas.save(lpath, 'PNG')
            ok += 1

        except Exception as e:
            print(f"\n  [!] Loi embed: {layer['local_path']}: {e}")
            err += 1

        total += 1
        if total % 200 == 0:
            sys.stdout.write(f"\r  embed {total}... ok={ok} skip={skip} err={err}   ")
            sys.stdout.flush()

    print(f"\r  embed {total} anh: xu ly={ok}  bo qua={skip}  loi={err}          ")


# ─────────────────────────────────────────────────────────────────────────────
# Tao viewer.html
# ─────────────────────────────────────────────────────────────────────────────

VIEWER_HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meiker Viewer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #1a1a2e; color: #eee; font-family: 'Segoe UI', sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #panel { width: 260px; min-width: 220px; background: #16213e; display: flex; flex-direction: column; border-right: 1px solid #0f3460; overflow: hidden; }
  #panel-header { padding: 12px 14px 8px; background: #0f3460; font-size: 13px; font-weight: 600; color: #e94560; letter-spacing: 0.5px; }
  #cat-tabs { display: flex; flex-wrap: wrap; gap: 4px; padding: 8px; overflow-y: auto; max-height: 140px; border-bottom: 1px solid #0f3460; }
  .cat-tab { padding: 4px 8px; border-radius: 4px; background: #0f3460; font-size: 11px; cursor: pointer; border: 1px solid transparent; transition: all .15s; white-space: nowrap; }
  .cat-tab:hover { background: #1a4a80; }
  .cat-tab.active { background: #e94560; border-color: #ff6b8a; color: #fff; }
  #options-title { padding: 8px 12px 4px; font-size: 11px; color: #aaa; text-transform: uppercase; letter-spacing: 0.5px; }
  #options-grid { flex: 1; overflow-y: auto; padding: 6px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; align-content: start; }
  .opt-thumb { aspect-ratio: 1; background: #0f3460; border-radius: 6px; overflow: hidden; cursor: pointer; border: 2px solid transparent; transition: border-color .15s; position: relative; display: flex; align-items: center; justify-content: center; }
  .opt-thumb:hover { border-color: #4a90d9; }
  .opt-thumb.selected { border-color: #e94560; }
  .opt-thumb.none-opt { background: #0a2240; }
  .opt-thumb.none-opt span { font-size: 18px; color: #555; }
  .opt-thumb img { width: 100%; height: 100%; object-fit: contain; image-rendering: pixelated; }
  .opt-label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,.55); font-size: 9px; text-align: center; padding: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #canvas-area { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 16px; overflow: hidden; }
  #canvas-wrap { position: relative; background: transparent; box-shadow: 0 8px 32px rgba(0,0,0,.5); border-radius: 4px; overflow: hidden; transform-origin: top center; }
  #canvas-wrap img.layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
  #toolbar { display: flex; gap: 10px; }
  .btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 13px; font-weight: 600; transition: opacity .15s; }
  .btn:hover { opacity: .85; }
  .btn-reset { background: #0f3460; color: #eee; }
  .btn-save  { background: #e94560; color: #fff; }
  #scale-label { font-size: 11px; color: #666; text-align: center; }
</style>
</head>
<body>
<div id="panel">
  <div id="panel-header">🎨 Meiker Viewer</div>
  <div id="cat-tabs"></div>
  <div id="options-title">Options</div>
  <div id="options-grid"></div>
</div>
<div id="canvas-area">
  <div id="canvas-wrap"></div>
  <div id="toolbar">
    <button class="btn btn-reset" onclick="resetAll()">↺ Reset</button>
    <button class="btn btn-save"  onclick="saveImage()">💾 Luu PNG</button>
  </div>
  <div id="scale-label"></div>
</div>
<script>
let manifest = null, selected = {}, activeCat = 0;

async function init() {
  manifest = await (await fetch('manifest.json')).json();
  document.querySelector('#panel-header').textContent = '🎨 ' + manifest.name;
  fitCanvas(); window.addEventListener('resize', fitCanvas);
  buildCatTabs(); selectCat(0);
  autoSelect(); renderCanvas(); buildOptionsGrid(0);
}

function fitCanvas() {
  const wrap = document.getElementById('canvas-wrap');
  const area = document.getElementById('canvas-area');
  const cw = manifest ? (manifest.canvas_width || 600) : 600;
  const ch = manifest ? (manifest.canvas_height || 800) : 800;
  wrap.style.width  = cw + 'px';
  wrap.style.height = ch + 'px';
  const scale = Math.min((area.clientHeight - 80) / ch, (area.clientWidth - 20) / cw, 1);
  wrap.style.transform = 'scale(' + scale + ')';
  wrap.style.marginBottom = ((scale - 1) * ch) + 'px';
  document.getElementById('scale-label').textContent =
    'Canvas: ' + cw + ' x ' + ch + ' px  |  hien thi ' + Math.round(scale * 100) + '%';
}

function buildCatTabs() {
  const tabs = document.getElementById('cat-tabs');
  tabs.innerHTML = '';
  manifest.categories.forEach((cat, i) => {
    const t = document.createElement('div');
    t.className = 'cat-tab'; t.textContent = cat.label;
    t.title = cat.type + ' | ' + cat.options.length + ' options';
    t.onclick = () => selectCat(i); t.id = 'tab-' + i;
    tabs.appendChild(t);
  });
}

function selectCat(i) {
  activeCat = i;
  document.querySelectorAll('.cat-tab').forEach((t, idx) => t.classList.toggle('active', idx === i));
  buildOptionsGrid(i);
}

function buildOptionsGrid(catIdx) {
  const cat  = manifest.categories[catIdx];
  const grid = document.getElementById('options-grid');
  document.getElementById('options-title').textContent = cat.label + '  (' + cat.options.length + ' options)';
  grid.innerHTML = '';
  if (cat.is_optional || cat.type === 'stamps') {
    const none = document.createElement('div');
    none.className = 'opt-thumb none-opt' + (selected[catIdx] === null ? ' selected' : '');
    none.innerHTML = '<span>X</span>'; none.title = 'Bo chon';
    none.onclick = () => { selected[catIdx] = null; renderCanvas(); buildOptionsGrid(catIdx); };
    grid.appendChild(none);
  }
  cat.options.forEach((opt, oi) => {
    const div = document.createElement('div');
    div.className = 'opt-thumb' + (selected[catIdx] === oi ? ' selected' : '');
    div.title = opt.label;
    const img = document.createElement('img');
    img.src = opt.thumbnail; img.alt = opt.label; img.loading = 'lazy';
    div.appendChild(img);
    const lbl = document.createElement('div');
    lbl.className = 'opt-label'; lbl.textContent = opt.label;
    div.appendChild(lbl);
    div.onclick = () => { selected[catIdx] = oi; renderCanvas(); buildOptionsGrid(catIdx); };
    grid.appendChild(div);
  });
}

// Render theo dung thu tu z tu render_order
function renderCanvas() {
  const wrap = document.getElementById('canvas-wrap');
  wrap.querySelectorAll('img.layer').forEach(el => el.remove());

  const renderOrder  = manifest.render_order  || [];
  const staticLayers = manifest.static_layers || [];

  // Fallback: neu khong co render_order thi render theo thu tu cu
  if (!renderOrder.length) {
    manifest.categories.forEach((cat, ci) => {
      const oi = selected[ci];
      if (oi === undefined || oi === null) return;
      cat.options[oi].layers.forEach(layer => addLayerImg(wrap, layer.local_path));
    });
    return;
  }

  renderOrder.forEach(entry => {
    if (entry.type === 'static') {
      // Render tat ca layers cua static node nay
      const sl = staticLayers[entry.index];
      if (!sl) return;
      sl.layers.forEach(layer => addLayerImg(wrap, layer.local_path));

    } else if (entry.type === 'category') {
      const ci  = entry.index;
      const oi  = selected[ci];
      if (oi === undefined || oi === null) return;
      const cat = manifest.categories[ci];
      if (!cat) return;
      cat.options[oi].layers.forEach(layer => addLayerImg(wrap, layer.local_path));
    }
  });
}

function addLayerImg(wrap, src) {
  const img = document.createElement('img');
  img.className = 'layer';
  img.src = src;
  img.draggable = false;
  wrap.appendChild(img);
}

function resetAll() { selected = {}; renderCanvas(); buildOptionsGrid(activeCat); }

function autoSelect() {
  manifest.categories.forEach((cat, ci) => {
    if (cat.type === 'icon-set' || cat.type === 'category') selected[ci] = 0;
  });
}

function saveImage() {
  const cw = manifest.canvas_width || 600, ch = manifest.canvas_height || 800;
  const cv = document.createElement('canvas');
  cv.width = cw; cv.height = ch;
  const ctx = cv.getContext('2d');

  // Thu thap layers theo dung thu tu render_order
  const renderOrder  = manifest.render_order  || [];
  const staticLayers = manifest.static_layers || [];
  const layerPaths   = [];

  if (renderOrder.length) {
    renderOrder.forEach(entry => {
      if (entry.type === 'static') {
        const sl = staticLayers[entry.index];
        if (sl) sl.layers.forEach(l => layerPaths.push(l.local_path));
      } else {
        const ci = entry.index, oi = selected[ci];
        if (oi === undefined || oi === null) return;
        const cat = manifest.categories[ci];
        if (cat) cat.options[oi].layers.forEach(l => layerPaths.push(l.local_path));
      }
    });
  } else {
    manifest.categories.forEach((cat, ci) => {
      const oi = selected[ci];
      if (oi === undefined || oi === null) return;
      cat.options[oi].layers.forEach(l => layerPaths.push(l.local_path));
    });
  }

  if (!layerPaths.length) { alert('Chua chon gi ca!'); return; }

  let loaded = 0;
  const imgs = layerPaths.map(p => {
    const i = new Image(); i.src = p + '?' + Date.now(); return i;
  });
  imgs.forEach(img => {
    img.onload = img.onerror = () => {
      if (++loaded < imgs.length) return;
      imgs.forEach(i => ctx.drawImage(i, 0, 0));
      const a = document.createElement('a');
      a.download = 'meiker_' + manifest.game_id + '.png';
      a.href = cv.toDataURL('image/png'); a.click();
    };
  });
}

init();
</script>
</body>
</html>"""


def copy_viewer(save_dir, game_name):
    """Ghi viewer.html vao thu muc game."""
    vpath = os.path.join(save_dir, 'viewer.html')
    with open(vpath, 'w', encoding='utf-8') as f:
        f.write(VIEWER_HTML)
    print(f"[+] Da tao viewer.html")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def scrape_game(game_id):
    print(f"\n{'='*55}")
    print(f"  Game ID: {game_id}")
    print(f"{'='*55}\n")

    # 1. Fetch trang game
    url  = f"https://meiker.io/play/{game_id}/online.html"
    html = fetch_with_curl(url)
    if not html:
        print("[!] Khong lay duoc trang game.")
        return

    # 2. Parse config
    config = extract_game_config(html, game_id)
    if not config:
        return

    game_name = config['name']
    print(f"[+] Game: {game_name}")

    # 3. Tao thu muc goc
    save_dir = os.path.join(os.getcwd(), 'downloads', f"meiker_{game_id}")
    os.makedirs(save_dir, exist_ok=True)

    # 4. Fetch raw_data.json
    print("\n[+] Dang lay du lieu...")
    raw_str = fetch_with_curl(config['data_url'])
    if not raw_str:
        return
    raw_data = json.loads(raw_str)

    # 5. Phan tich cau truc
    print("[+] Dang phan tich cau truc bo phan...")
    manifest_cats, static_layers, render_order, id_to_path, all_downloads = analyze_structure(raw_data)
    print(f"    -> {len(manifest_cats)} categories | {len(static_layers)} static layers | {len(all_downloads)} anh can tai")

    # 6. Luu manifest.json
    manifest = {
        'game_id':      game_id,
        'name':         game_name,
        'canvas_width': config.get('canvas_width'),
        'canvas_height':config.get('canvas_height'),
        'categories':   manifest_cats,
        'static_layers': static_layers,
        'render_order':  render_order,
    }
    with open(os.path.join(save_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[+] Da luu manifest.json")
    print(f"[+] Da tao xong cau truc!")

    # 7. Tao truoc tat ca folder
    all_folders = set()
    for cat in manifest_cats:
        for opt in cat['options']:
            all_folders.add(os.path.join(save_dir, opt['folder']))
    # Tao folder static
    all_folders.add(os.path.join(save_dir, 'static'))
    for folder in all_folders:
        os.makedirs(folder, exist_ok=True)

    # 9. Download tat ca anh
    total = len(all_downloads)
    print(f"\n[+] Bat dau tai {total} anh...")

    def do_download(entry):
        fpath = os.path.join(save_dir, entry['local_path'])
        ok, msg = download_file(entry['cdn_url'], fpath)
        return ok, msg, entry['local_path']

    ok_count = err_count = skip_count = 0
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
        futures = [pool.submit(do_download, e) for e in all_downloads]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            ok, msg, lpath = fut.result()
            if ok:
                skip_count += (msg == "skip")
                ok_count   += (msg != "skip")
            else:
                err_count += 1
                print(f"\n[!] Loi: {lpath} -> {msg}")
            if i % 50 == 0 or i == total:
                sys.stdout.write(f"\r  {i}/{total}  ok={ok_count}  skip={skip_count}  err={err_count}   ")
                sys.stdout.flush()

    elapsed = time.time() - start
    print(f"\n\n{'='*55}")
    print(f"  Hoan thanh trong {elapsed:.1f}s")
    print(f"  Tai moi: {ok_count} | Bo qua: {skip_count} | Loi: {err_count}")
    print(f"{'='*55}\n")

    # 10. Embed tung anh vao canvas canvas_width x canvas_height
    cw = manifest['canvas_width']  or 600
    ch = manifest['canvas_height'] or 800
    embed_layers(manifest_cats, static_layers, save_dir, cw, ch)

    # 11. Tao viewer.html
    copy_viewer(save_dir, game_name)

    print(f"\n{'='*55}")
    print(f"  Thu muc: {save_dir}")
    print(f"\n  Folder da tao:")
    for cat in manifest_cats:
        print(f"    {cat['folder']}/  [{cat['label']}]  {len(cat['options'])} options")
    print(f"\n  Mo viewer: http://localhost/meiker/downloads/meiker_{game_id}/viewer.html")
    print(f"{'='*55}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Dung: python meiker_scraper.py <game_id>")
        print("Vi du: python meiker_scraper.py 18554")
        sys.exit(1)
    gid = sys.argv[1].strip()
    if not gid.isdigit():
        print("Loi: Game ID phai la so.")
        sys.exit(1)
    scrape_game(gid)
