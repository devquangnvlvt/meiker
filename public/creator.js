/**
 * Meiker Character Creator (Local Mode)
 * Reads manifest.json (scraper v2 output) for proper category → option → layers structure.
 * Falls back to ui_config.json (scraper v1) if manifest.json not found.
 */

const GAME_ID   = new URLSearchParams(location.search).get('id') || "18554";
const LOCAL_BASE = `/downloads/meiker_${GAME_ID}/`;

// ── STATE ─────────────────────────────────────────────────────────────────────
let manifest      = null;   // manifest.json
let flatLayerList = [];     // flattened list of all layers (for rendering order)

// Selection state
let selOption     = {};     // { catIdx: optionIndex | null }
let activeCatIdx  = 0;
let uiCats        = [];     // manifest.categories

let renderBusy    = false;
let renderQueued  = false;

const canvas   = document.getElementById("mainCanvas");
const ctx      = canvas.getContext("2d");
const imgCache = {};

// ── INIT ──────────────────────────────────────────────────────────────────────
async function init() {
  setLoading("Loading assets...");
  try {
    // 1. Load manifest.json
    const mfRes = await fetch(`${LOCAL_BASE}manifest.json`);
    if (!mfRes.ok) throw new Error("manifest.json not found!");
    manifest = await mfRes.json();

    // Update page title
    document.title = `${manifest.name} – Meiker Creator`;
    const titleEl = document.getElementById('gameTitle');
    if (titleEl) titleEl.textContent = `🎨 ${manifest.name}`;

    // 2. Build flat z-order list from manifest
    // Since categories are ordered by Z-index, and options/layers inside are ordered,
    // we can just flatten them to get a master rendering list.
    (manifest.categories || []).forEach(cat => {
      cat.options.forEach(opt => {
        opt.layers.forEach(layer => {
          flatLayerList.push(layer);
        });
      });
    });

    // 3. Build initial selection state (Show ALL categories including fixed ones)
    uiCats = manifest.categories || [];
    uiCats.forEach((cat, idx) => {
      // Default: select first visible option, or null if optional
      const firstVisible = cat.options.findIndex(o => o.visible);
      if (cat.is_optional) {
        selOption[idx] = firstVisible >= 0 ? firstVisible : null;
      } else {
        selOption[idx] = firstVisible >= 0 ? firstVisible : (cat.options.length > 0 ? 0 : null);
      }
    });

    setLoading("Building UI...");
    buildUI();

    setLoading("Rendering...");
    await renderCanvas();
    hideLoader();
  } catch (e) {
    document.getElementById("loadingOverlay").innerHTML =
      `<div style="color:#f87171;font-size:14px;padding:24px;text-align:center;line-height:1.8">
       ❌ ${e.message.replace(/\n/g,'<br>')}
       </div>`;
  }
}

function setLoading(msg) {
  const el = document.getElementById("loaderText");
  if (el) el.textContent = msg;
}

function hideLoader() {
  const o = document.getElementById("loadingOverlay");
  if (o) { o.classList.add("fade-out"); setTimeout(() => o.remove(), 600); }
}

// ── BUILD UI ──────────────────────────────────────────────────────────────────
function buildUI() {
  const tabsEl = document.getElementById("catTabs");
  tabsEl.innerHTML = "";

  uiCats.forEach((cat, i) => {
    const btn = document.createElement("button");
    btn.className = "cat-tab";
    btn.dataset.idx = i;

    const firstOpt = cat.options[0];
    const thumb = firstOpt?.thumbnail;
    if (thumb) {
      btn.innerHTML = `<img src="${LOCAL_BASE}${thumb}" style="width:22px;height:22px;border-radius:4px;object-fit:cover;vertical-align:middle;margin-right:4px" onerror="this.remove()">${cat.folder}`;
    } else {
      btn.textContent = cat.folder;
    }

    tabsEl.appendChild(btn);
  });

  tabsEl.onclick = (e) => {
    const btn = e.target.closest(".cat-tab");
    if (!btn) return;
    selectCat(parseInt(btn.dataset.idx));
  };

  if (uiCats.length > 0) selectCat(0);
}

function selectCat(idx) {
  activeCatIdx = idx;
  document.querySelectorAll(".cat-tab")
    .forEach((t, i) => t.classList.toggle("active", i === idx));
  renderPanel(uiCats[idx], idx);
}

// ── PANEL RENDERING ───────────────────────────────────────────────────────────
function renderPanel(cat, catIdx) {
  const el = document.getElementById("panelContent");
  el.innerHTML = "";

  // "None" option for optional categories
  if (cat.is_optional) {
    const strip = div("toggle-strip");
    const offBtn = document.createElement("button");
    offBtn.className = "badge-toggle" + (selOption[catIdx] === null ? " on" : "");
    offBtn.textContent = "✕ None";
    offBtn.onclick = () => {
      selOption[catIdx] = null;
      el.querySelectorAll(".item-thumb").forEach(t => t.classList.remove("active"));
      offBtn.classList.add("on");
      queueRender();
    };
    strip.appendChild(offBtn);
    const cnt = document.createElement("span");
    cnt.style.cssText = "font-size:11px;color:var(--text-muted);margin-left:8px";
    cnt.textContent = `${cat.options.length} options`;
    strip.appendChild(cnt);
    el.appendChild(strip);
  }

  if (cat.options.length === 0) {
    el.insertAdjacentHTML("beforeend",
      `<p style="color:var(--text-muted);padding:16px;font-size:13px">No options in this category.</p>`);
    return;
  }

  const grid = div("items-grid");
  cat.options.forEach((opt, optIdx) => {
    const isActive = selOption[catIdx] === optIdx;
    const thumb = div("item-thumb" + (isActive ? " active" : ""));
    thumb.dataset.optIdx = optIdx;
    thumb.title = opt.label;

    const img = document.createElement("img");
    img.src = LOCAL_BASE + opt.thumbnail;
    img.alt = opt.label;
    img.loading = "lazy";
    img.onerror = () => { thumb.style.background = "var(--bg-hover)"; img.remove(); };

    const lbl = document.createElement("div");
    lbl.className = "item-label";
    lbl.textContent = opt.label;

    thumb.appendChild(img);
    thumb.appendChild(lbl);
    thumb.onclick = () => {
      selOption[catIdx] = optIdx;
      grid.querySelectorAll(".item-thumb").forEach(t => t.classList.remove("active"));
      thumb.classList.add("active");
      el.querySelectorAll(".badge-toggle").forEach(b => b.classList.remove("on"));
      queueRender();
    };
    grid.appendChild(thumb);
  });
  el.appendChild(grid);
}

function div(cls) {
  const el = document.createElement("div");
  el.className = cls;
  return el;
}

// ── CANVAS RENDER ─────────────────────────────────────────────────────────────
function queueRender() {
  if (renderBusy) { renderQueued = true; return; }
  renderCanvas();
}

async function renderCanvas() {
  if (renderBusy) { renderQueued = true; return; }
  renderBusy = true;
  renderQueued = false;

  const wrap  = document.getElementById("canvasWrap");
  const maxW  = wrap.clientWidth  || 600;
  const maxH  = wrap.clientHeight || 800;
  const gameW = manifest?.canvas_width  || 600;
  const gameH = manifest?.canvas_height || 800;
  const s     = Math.min(maxW / gameW, maxH / gameH, 1);

  canvas.width  = Math.round(gameW * s);
  canvas.height = Math.round(gameH * s);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.scale(s, s);

  // Build a Set of image IDs that should be visible right now
  const visibleIds = buildVisibleSet();

  let drawn = 0;
  for (const layer of flatLayerList) {
    if (!visibleIds.has(layer.id)) continue;
    if (!layer.local_path) continue;
    await drawLayer(layer, LOCAL_BASE + layer.local_path);
    drawn++;
  }

  ctx.restore();
  console.log(`Rendered ${drawn} layers @ scale=${s.toFixed(2)}`);
  renderBusy = false;
  if (renderQueued) renderCanvas();
}

/**
 * Build a Set of image node IDs that are "selected/active" right now.
 * Uses manifest structure: for each category, find selected option, collect its layer IDs.
 * Also includes all static layer IDs.
 */
function buildVisibleSet() {
  const ids = new Set();

  // 1. Static layers from manifest — SKIP them.
  // These are game background panels (solid color fills used by meiker's UI),
  // NOT character parts. Including them blocks the character view.
  // if (manifest?.static) {
  //   manifest.static.forEach(s => ids.add(s.id));
  // }

  // 2. Add layers from FIXED categories (e.g. base body parts)
  // Since fixed categories are NOT in uiCats (they are hidden from tabs),
  // we must iterate over the full manifest categories to render them.
  (manifest?.categories || []).forEach(cat => {
    if (cat.is_fixed) {
      cat.options.forEach(opt => {
        opt.layers.forEach(layer => ids.add(layer.id));
      });
    }
  });

  // 3. Add layers from UI categories (optional/chooser)
  uiCats.forEach((cat, uiIdx) => {
    const optIdx = selOption[uiIdx];
    if (optIdx === null || optIdx === undefined) return;
    const opt = cat.options[optIdx];
    if (!opt) return;
    opt.layers.forEach(layer => ids.add(layer.id));
  });

  return ids;
}

// ── DRAW LAYER ────────────────────────────────────────────────────────────────
async function drawLayer(layer, localPath) {
  try {
    const img = await loadImage(localPath);
    ctx.globalAlpha = layer.opacity ?? 1;
    ctx.drawImage(img, layer.x ?? 0, layer.y ?? 0);
    ctx.globalAlpha = 1;
  } catch (_) { /* silently skip missing images */ }
}

function loadImage(url) {
  if (imgCache[url]) {
    return imgCache[url].complete
      ? Promise.resolve(imgCache[url])
      : new Promise((res, rej) => {
          imgCache[url].onload  = () => res(imgCache[url]);
          imgCache[url].onerror = rej;
        });
  }
  return new Promise((resolve, reject) => {
    const img = new Image();
    imgCache[url] = img;
    img.onload  = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
}

// ── ACTIONS ───────────────────────────────────────────────────────────────────
function saveImage() {
  const link = document.createElement("a");
  link.download = `meiker_${GAME_ID}_${Date.now()}.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();
}

function randomize() {
  uiCats.forEach((cat, catIdx) => {
    if (cat.options.length === 0) return;
    if (cat.is_optional && Math.random() < 0.3) {
      selOption[catIdx] = null;
    } else {
      selOption[catIdx] = Math.floor(Math.random() * cat.options.length);
    }
  });
  renderPanel(uiCats[activeCatIdx], activeCatIdx);
  queueRender();
}

function resetAll() {
  uiCats.forEach((cat, idx) => {
    const firstVisible = cat.options.findIndex(o => o.visible);
    selOption[idx] = cat.is_optional
      ? (firstVisible >= 0 ? firstVisible : null)
      : (firstVisible >= 0 ? firstVisible : (cat.options.length > 0 ? 0 : null));
  });
  renderPanel(uiCats[activeCatIdx], activeCatIdx);
  queueRender();
}

// ── ZOOM ──────────────────────────────────────────────────────────────────────
let zoomLevel = 1;
function zoomIn()    { zoomLevel = Math.min(zoomLevel + 0.15, 3);   applyZoom(); }
function zoomOut()   { zoomLevel = Math.max(zoomLevel - 0.15, 0.3); applyZoom(); }
function zoomReset() { zoomLevel = 1; applyZoom(); }
function applyZoom() {
  canvas.style.transform = `scale(${zoomLevel})`;
  canvas.style.transformOrigin = "top left";
}

window.addEventListener("resize", debounce(queueRender, 300));
function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

init();
