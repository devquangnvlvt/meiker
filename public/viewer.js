const GAME_ID = "18554";
const BASE_URL = "https://cdn.meiker.io/";

let rawData = null;
let uiConfig = null;

// Map of url-hash -> { localPath, cdnUrl }
let assetMap = {};

// { [category]: { [color]: { [label]: [assets] } } }
let uiData = {};

let activeCategory = null;
let activeColor = null;

let uiAssetHashes = new Set();
let activeUrls = new Set();
let renderSequence = [];

document.addEventListener("DOMContentLoaded", init);

async function init() {
  setLoading(true);
  await loadData();
  buildUIData();
  initializeActiveUrls();
  buildSequence();
  renderCategoryTabs();
  renderCanvas();
  setLoading(false);

  document.getElementById("btn-random").addEventListener("click", randomize);
  document.getElementById("btn-reset").addEventListener("click", reset);
  document
    .getElementById("btn-download")
    .addEventListener("click", downloadCanvas);
}

function setLoading(v) {
  document.getElementById("loading").classList.toggle("hidden", !v);
}

function resolveUrl(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path.split("?")[0];
  if (path.startsWith("//")) return ("https:" + path).split("?")[0];
  return (BASE_URL.replace(/\/$/, "") + "/" + path.replace(/^\//, "")).split(
    "?",
  )[0];
}

function cleanFilename(name) {
  if (!name) return "";
  return String(name)
    .replace(/#/g, "")
    .replace(/[^\w\-\. ]/g, "_");
}

function getHashKey(url) {
  if (!url) return "";
  return url.split("/").pop().split("?")[0];
}

// ──────────────────────────────────────────────
// DATA LOADING
// ──────────────────────────────────────────────
async function loadData() {
  try {
    const r = await fetch(`/downloads/meiker_${GAME_ID}/raw_data.json`);
    rawData = await r.json();
  } catch (e) {
    alert("Failed to load raw_data.json");
  }

  try {
    const r = await fetch(`/downloads/meiker_${GAME_ID}/ui_config.json`);
    uiConfig = await r.json();

    if (uiConfig.assets) {
      uiConfig.assets.forEach((asset) => {
        const cat = asset.category || "misc";
        const col = asset.color || "";
        const file = asset.filename;

        let localPath = `/downloads/meiker_${GAME_ID}/${cleanFilename(cat)}`;
        if (col) localPath += `/${cleanFilename(col)}`;
        localPath += `/${file}`;

        const cdnUrl = resolveUrl(asset.url);
        const hash = getHashKey(asset.url);
        assetMap[hash] = { localPath, cdnUrl };
        uiAssetHashes.add(hash);
      });
    }
  } catch (e) {
    console.warn("No ui_config.json", e);
  }
}

function buildUIData() {
  uiData = {};
  if (!uiConfig || !uiConfig.assets) return;

  uiConfig.assets.forEach((asset) => {
    const cat = asset.category || "misc";
    const col = asset.color || "default";
    let label = asset.label || "Item";

    // Group layers by stripping _L1 / _1 suffix
    let baseLabel = label;
    const lMatch = label.match(/^(.*?)_L\d+$/);
    const nMatch = label.match(/^(.*?)_\d+$/);
    if (lMatch) baseLabel = lMatch[1];
    else if (nMatch) baseLabel = nMatch[1];

    if (!uiData[cat]) uiData[cat] = {};
    if (!uiData[cat][col]) uiData[cat][col] = {};
    if (!uiData[cat][col][baseLabel]) uiData[cat][col][baseLabel] = [];
    uiData[cat][col][baseLabel].push(asset);
  });
}

function initializeActiveUrls() {
  activeUrls.clear();

  function traverse(nodes) {
    if (!Array.isArray(nodes)) return;
    nodes.forEach((node) => {
      if (node.visible && node.type === "image" && node.image) {
        activeUrls.add(getHashKey(resolveUrl(node.image)));
      }
      // Auto-select first child of icon-sets if none are visible
      if (
        (node.type === "icon-set" || node.type === "color-picker") &&
        node.visible !== false
      ) {
        const visibleChild = (node.children || []).find(
          (c) => c.visible && c.type === "image",
        );
        if (!visibleChild && node.children && node.children.length > 0) {
          const first = node.children.find((c) => c.type === "image");
          if (first) activeUrls.add(getHashKey(resolveUrl(first.image)));
        }
      }
      if (node.children) traverse(node.children);
    });
  }

  if (Array.isArray(rawData)) traverse(rawData);
}

function buildSequence() {
  renderSequence = [];

  function walk(nodes) {
    if (!Array.isArray(nodes)) return;
    nodes.forEach((node) => {
      if (node.type === "image" && node.image) {
        renderSequence.push({
          hash: getHashKey(resolveUrl(node.image)),
          rawUrl: resolveUrl(node.image),
          x: node.x || 0,
          y: node.y || 0,
        });
      }
      if (node.children) walk(node.children);
    });
  }
  walk(rawData);
}

// ──────────────────────────────────────────────
// CATEGORY TABS
// ──────────────────────────────────────────────
function renderCategoryTabs() {
  const container = document.getElementById("tabs-container");
  container.innerHTML = "";

  const categories = Object.keys(uiData).sort();
  categories.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "tab-btn";
    btn.textContent = cat;
    btn.onclick = () => selectCategory(cat);
    container.appendChild(btn);
  });

  if (categories.length > 0) selectCategory(categories[0]);
}

function selectCategory(cat) {
  activeCategory = cat;

  document
    .querySelectorAll(".tab-btn")
    .forEach((b) => b.classList.toggle("active", b.textContent === cat));

  const colors = Object.keys(uiData[cat] || {});
  if (!colors.includes(activeColor)) activeColor = colors[0] || "default";

  renderColorPanel();
  renderItemsGrid();
}

// ──────────────────────────────────────────────
// LEFT COLOR PANEL
// ──────────────────────────────────────────────
function renderColorPanel() {
  const list = document.getElementById("color-panel-list");
  list.innerHTML = "";

  if (!activeCategory || !uiData[activeCategory]) return;

  const colors = Object.keys(uiData[activeCategory]);

  // Only show if multiple colors exist
  if (colors.length <= 1 && colors[0] === "default") return;

  colors.forEach((col) => {
    const circle = document.createElement("div");
    circle.className = `color-circle${col === activeColor ? " active" : ""}`;

    // Resolve color to a CSS background
    const hex6 = /^[0-9A-Fa-f]{6}$/.test(col);
    if (hex6) circle.style.background = "#" + col;
    else if (col.startsWith("#")) circle.style.background = col;
    else circle.style.background = "#999";

    circle.title = col;
    circle.onclick = () => selectColor(col);
    list.appendChild(circle);
  });
}

function selectColor(col) {
  activeColor = col;
  document.querySelectorAll(".color-circle").forEach((c, i) => {
    c.classList.toggle(
      "active",
      Object.keys(uiData[activeCategory])[i] === col,
    );
  });
  renderItemsGrid();
}

// ──────────────────────────────────────────────
// ITEMS GRID (two columns: dot + card)
// ──────────────────────────────────────────────
function renderItemsGrid() {
  const grid = document.getElementById("items-grid");
  grid.innerHTML = "";

  if (!uiData[activeCategory] || !uiData[activeCategory][activeColor]) return;

  const items = uiData[activeCategory][activeColor];

  Object.keys(items).forEach((label) => {
    const itemAssets = items[label];
    const primary = itemAssets[0];
    const entry = assetMap[getHashKey(primary.url)];
    const imgSrc = entry ? entry.localPath : resolveUrl(primary.url);
    const cdnSrc = entry ? entry.cdnUrl : resolveUrl(primary.url);

    const isActive = itemAssets.every((a) =>
      activeUrls.has(getHashKey(resolveUrl(a.url))),
    );

    // Left column – color dot
    const dot = document.createElement("div");
    dot.className = "item-color-dot";
    const hex6 = /^[0-9A-Fa-f]{6}$/.test(activeColor);
    if (hex6) dot.style.background = "#" + activeColor;
    else if (activeColor.startsWith("#")) dot.style.background = activeColor;
    else dot.style.background = "rgba(255,255,255,0.15)";
    dot.onclick = () => toggleItem(itemAssets);

    // Right column – item card
    const card = document.createElement("div");
    card.className = `item-card${isActive ? " active" : ""}`;

    const img = document.createElement("img");
    img.src = imgSrc;
    img.alt = label;
    img.loading = "lazy";
    img.onerror = function () {
      this.onerror = null;
      this.src = cdnSrc;
    };

    const lbl = document.createElement("div");
    lbl.className = "item-label";
    lbl.textContent = label;

    card.appendChild(img);
    card.appendChild(lbl);
    card.onclick = () => toggleItem(itemAssets);

    grid.appendChild(dot);
    grid.appendChild(card);
  });
}

function toggleItem(itemAssets) {
  const isActive = itemAssets.every((a) =>
    activeUrls.has(getHashKey(resolveUrl(a.url))),
  );

  if (isActive) {
    itemAssets.forEach((a) => activeUrls.delete(getHashKey(resolveUrl(a.url))));
  } else {
    // Deselect siblings in same category
    const siblings = [];
    Object.values(uiData[activeCategory] || {}).forEach((colGroup) =>
      Object.values(colGroup).forEach((assets) =>
        assets.forEach((a) => siblings.push(a)),
      ),
    );
    siblings.forEach((a) => activeUrls.delete(getHashKey(resolveUrl(a.url))));

    itemAssets.forEach((a) => activeUrls.add(getHashKey(resolveUrl(a.url))));
  }

  renderItemsGrid();
  renderCanvas();
}

// ──────────────────────────────────────────────
// CANVAS RENDERING
// ──────────────────────────────────────────────
function renderCanvas() {
  const container = document.getElementById("canvas-container");
  container.innerHTML = "";

  if (uiConfig && uiConfig.canvas_width) {
    container.style.width = uiConfig.canvas_width + "px";
    container.style.height = uiConfig.canvas_height + "px";

    // Scale to fit the viewport
    const maxH = window.innerHeight - 100;
    const maxW = container.parentElement.offsetWidth - 40;
    const fitW =
      uiConfig.canvas_width > maxW ? maxW / uiConfig.canvas_width : 1;
    const fitH =
      uiConfig.canvas_height > maxH ? maxH / uiConfig.canvas_height : 1;
    const scale = Math.min(fitW, fitH, 1);
    container.style.transform = scale < 1 ? `scale(${scale})` : "";
    container.style.transformOrigin = "top center";
  }

  renderSequence.forEach((node) => {
    if (!activeUrls.has(node.hash)) return;

    const entry = assetMap[node.hash];
    const src = entry ? entry.localPath : node.rawUrl;
    const fallback = entry ? entry.cdnUrl : node.rawUrl;

    const img = document.createElement("img");
    img.src = src;
    img.onerror = function () {
      this.onerror = null;
      this.src = fallback;
    };
    img.style.position = "absolute";
    img.style.left = node.x + "px";
    img.style.top = node.y + "px";
    container.appendChild(img);
  });
}

// ──────────────────────────────────────────────
// ACTIONS
// ──────────────────────────────────────────────
function randomize() {
  Array.from(activeUrls).forEach((hash) => {
    if (uiAssetHashes.has(hash)) activeUrls.delete(hash);
  });

  Object.keys(uiData).forEach((cat) => {
    const colors = Object.keys(uiData[cat]);
    const rCol = colors[Math.floor(Math.random() * colors.length)];
    const itemGroups = Object.values(uiData[cat][rCol] || {});
    if (itemGroups.length > 0) {
      const pick = itemGroups[Math.floor(Math.random() * itemGroups.length)];
      pick.forEach((a) => activeUrls.add(getHashKey(resolveUrl(a.url))));
    }
  });

  renderItemsGrid();
  renderColorPanel();
  renderCanvas();
}

function reset() {
  initializeActiveUrls();
  renderItemsGrid();
  renderCanvas();
}

function downloadCanvas() {
  const container = document.getElementById("canvas-container");
  html2canvas(container, {
    backgroundColor: null,
    scale: 2,
    useCORS: true,
  }).then((canvas) => {
    const a = document.createElement("a");
    a.download = "meiker_character.png";
    a.href = canvas.toDataURL("image/png");
    a.click();
  });
}
