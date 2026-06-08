// State
let gameConfig = null;
let gameData = null;
let selectedCategory = null;
let selectedItems = new Set();

// Enter key to search
document.getElementById('gameId').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') fetchGameData();
});

// Fetch game data
async function fetchGameData() {
    const gameId = document.getElementById('gameId').value.trim();
    if (!gameId) return;

    showLoading(true);
    hideError();
    hide('gameInfo');
    hide('dataContent');
    hide('rawJson');

    try {
        // Step 1: Get game config from the page
        const configRes = await fetch(`/api/game/${gameId}`);
        if (!configRes.ok) {
            const err = await configRes.json();
            throw new Error(err.error || `HTTP ${configRes.status}`);
        }
        gameConfig = await configRes.json();

        // Step 2: Fetch data.json
        const dataRes = await fetch(`/api/data?url=${encodeURIComponent(gameConfig.data_url)}`);
        if (!dataRes.ok) {
            const err = await dataRes.json();
            throw new Error(err.error || `HTTP ${dataRes.status}`);
        }
        gameData = await dataRes.json();

        // Display game info
        displayGameInfo();
        // Display categories and items
        displayCategories();
        // Show raw JSON
        displayRawJson();

    } catch (err) {
        showError(err.message);
    } finally {
        showLoading(false);
    }
}

function displayGameInfo() {
    document.getElementById('gameIcon').src = gameConfig.icon || '';
    document.getElementById('gameName').textContent = gameConfig.name;
    document.getElementById('gameOwner').textContent = `👤 ${gameConfig.owner?.nickname || 'Unknown'}`;
    document.getElementById('gameSize').textContent = `📐 ${gameConfig.canvas_width}×${gameConfig.canvas_height}`;
    document.getElementById('gameId_display').textContent = `🎮 ID: ${gameConfig.game_id}`;

    const tagsDiv = document.getElementById('gameTags');
    tagsDiv.innerHTML = '';
    if (gameConfig.tags && gameConfig.tags.length) {
        gameConfig.tags.forEach(t => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = t;
            tagsDiv.appendChild(span);
        });
    }

    show('gameInfo');
}

function displayCategories() {
    const tabsBar = document.getElementById('tabsBar');
    tabsBar.innerHTML = '';

    if (!gameData || !gameData.categories) {
        showError('Không tìm thấy categories trong data.json');
        return;
    }

    const categories = gameData.categories;
    categories.forEach((cat, index) => {
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        const itemCount = countItems(cat);
        btn.innerHTML = `${cat.name || cat.label || `Cat ${index}`} <span class="count">${itemCount}</span>`;
        btn.onclick = () => selectCategory(index, btn);
        tabsBar.appendChild(btn);
    });

    show('dataContent');

    // Auto-select first category
    if (categories.length > 0) {
        const firstBtn = tabsBar.querySelector('.tab-btn');
        selectCategory(0, firstBtn);
    }
}

function countItems(category) {
    let count = 0;
    if (category.items) count += category.items.length;
    if (category.subcategories) {
        category.subcategories.forEach(sub => {
            if (sub.items) count += sub.items.length;
        });
    }
    if (category.options) count += category.options.length;
    // For layers structure
    if (category.layers) {
        category.layers.forEach(layer => {
            if (layer.options) count += layer.options.length;
            if (layer.items) count += layer.items.length;
        });
    }
    return count;
}

function selectCategory(index, btnEl) {
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    selectedCategory = index;
    selectedItems.clear();
    updateSelectedCount();

    const cat = gameData.categories[index];
    document.getElementById('categoryTitle').textContent = cat.name || cat.label || `Category ${index}`;

    const grid = document.getElementById('itemsGrid');
    grid.innerHTML = '';

    // Collect all image items from this category
    const allItems = collectAllItems(cat);

    if (allItems.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); padding: 20px; text-align: center;">Không có items nào trong danh mục này</p>';
        return;
    }

    allItems.forEach((item, i) => {
        const card = createItemCard(item, i);
        grid.appendChild(card);
    });
}

function collectAllItems(category) {
    const items = [];
    const baseUrl = gameConfig.base_url || 'https://cdn.meiker.io/';

    // Direct items
    if (category.items) {
        category.items.forEach(item => {
            addItemImages(items, item, baseUrl, category.name || '');
        });
    }

    // Options (common in meiker data)
    if (category.options) {
        category.options.forEach(opt => {
            addItemImages(items, opt, baseUrl, category.name || '');
        });
    }

    // Subcategories
    if (category.subcategories) {
        category.subcategories.forEach(sub => {
            if (sub.items) {
                sub.items.forEach(item => {
                    addItemImages(items, item, baseUrl, sub.name || sub.label || '');
                });
            }
            if (sub.options) {
                sub.options.forEach(opt => {
                    addItemImages(items, opt, baseUrl, sub.name || sub.label || '');
                });
            }
        });
    }

    // Layers (meiker format: categories[].layers[].options[])
    if (category.layers) {
        category.layers.forEach(layer => {
            if (layer.options) {
                layer.options.forEach(opt => {
                    addItemImages(items, opt, baseUrl, layer.name || layer.label || '');
                });
            }
            if (layer.items) {
                layer.items.forEach(item => {
                    addItemImages(items, item, baseUrl, layer.name || layer.label || '');
                });
            }
        });
    }

    return items;
}

function addItemImages(items, item, baseUrl, subLabel) {
    // item can have: src, image, images, thumbnail, thumbnails, path, url
    const possibleKeys = ['src', 'image', 'path', 'url', 'thumbnail'];
    const label = item.name || item.label || item.id || item.value || '';

    // Single image reference
    for (const key of possibleKeys) {
        if (item[key] && typeof item[key] === 'string') {
            const imgUrl = resolveUrl(item[key], baseUrl);
            items.push({
                id: items.length,
                label: label || extractFilename(item[key]),
                subLabel: subLabel,
                url: imgUrl,
                thumbnailUrl: imgUrl,
                raw: item,
            });
            return; // Found primary image
        }
    }

    // Multiple images in arrays
    if (item.images && Array.isArray(item.images)) {
        item.images.forEach((img, idx) => {
            const imgUrl = typeof img === 'string' ? resolveUrl(img, baseUrl) : resolveUrl(img.src || img.url || img.path || '', baseUrl);
            items.push({
                id: items.length,
                label: `${label} #${idx + 1}`,
                subLabel: subLabel,
                url: imgUrl,
                thumbnailUrl: imgUrl,
                raw: item,
            });
        });
        return;
    }

    // Layers inside an option (nested structure)
    if (item.layers && Array.isArray(item.layers)) {
        item.layers.forEach((layer, idx) => {
            for (const key of possibleKeys) {
                if (layer[key] && typeof layer[key] === 'string') {
                    const imgUrl = resolveUrl(layer[key], baseUrl);
                    items.push({
                        id: items.length,
                        label: layer.name || `${label} L${idx + 1}`,
                        subLabel: subLabel,
                        url: imgUrl,
                        thumbnailUrl: imgUrl,
                        raw: layer,
                    });
                }
            }
        });
        if (items.length > 0) return;
    }

    // If nothing found but item has data, add it as metadata-only
    if (Object.keys(item).length > 0 && !item.src && !item.image && !item.path) {
        // Check all string values for image-like paths
        for (const [key, val] of Object.entries(item)) {
            if (typeof val === 'string' && (val.endsWith('.png') || val.endsWith('.jpg') || val.endsWith('.webp') || val.endsWith('.svg'))) {
                const imgUrl = resolveUrl(val, baseUrl);
                items.push({
                    id: items.length,
                    label: label || key,
                    subLabel: subLabel,
                    url: imgUrl,
                    thumbnailUrl: imgUrl,
                    raw: item,
                });
                return;
            }
        }
    }
}

function resolveUrl(path, baseUrl) {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    if (path.startsWith('//')) return 'https:' + path;
    return baseUrl.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
}

function extractFilename(url) {
    return url.split('/').pop().split('?')[0] || 'unknown';
}

function createItemCard(item, index) {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.dataset.index = index;

    card.innerHTML = `
        <div class="check">${selectedItems.has(index) ? '✓' : ''}</div>
        <img class="item-thumb" src="/api/image?url=${encodeURIComponent(item.thumbnailUrl)}" 
             alt="${item.label}" loading="lazy"
             onerror="this.style.display='none'">
        <div class="item-label" title="${item.subLabel ? item.subLabel + ' / ' : ''}${item.label}">
            ${item.label}
        </div>
    `;

    card.onclick = () => toggleItem(card, index);
    return card;
}

function toggleItem(card, index) {
    if (selectedItems.has(index)) {
        selectedItems.delete(index);
        card.classList.remove('selected');
        card.querySelector('.check').textContent = '';
    } else {
        selectedItems.add(index);
        card.classList.add('selected');
        card.querySelector('.check').textContent = '✓';
    }
    updateSelectedCount();
}

function selectAll() {
    const grid = document.getElementById('itemsGrid');
    grid.querySelectorAll('.item-card').forEach(card => {
        const idx = parseInt(card.dataset.index);
        selectedItems.add(idx);
        card.classList.add('selected');
        card.querySelector('.check').textContent = '✓';
    });
    updateSelectedCount();
}

function deselectAll() {
    const grid = document.getElementById('itemsGrid');
    grid.querySelectorAll('.item-card').forEach(card => {
        card.classList.remove('selected');
        card.querySelector('.check').textContent = '';
    });
    selectedItems.clear();
    updateSelectedCount();
}

function updateSelectedCount() {
    document.getElementById('selectedCount').textContent = selectedItems.size;
}

// Download selected items
async function downloadSelected() {
    if (selectedItems.size === 0) return;

    const cat = gameData.categories[selectedCategory];
    const allItems = collectAllItems(cat);
    const toDownload = [...selectedItems].map(i => allItems[i]).filter(Boolean);

    const images = toDownload.map(item => ({
        url: item.url,
        filename: extractFilename(item.url),
    }));

    await performDownload(images, cat.name || cat.label || 'misc');
}

// Download all data
async function downloadAllData() {
    if (!gameData || !gameData.categories) return;

    let allImages = [];
    gameData.categories.forEach(cat => {
        const items = collectAllItems(cat);
        items.forEach(item => {
            allImages.push({
                url: item.url,
                filename: extractFilename(item.url),
                category: cat.name || cat.label || 'all',
            });
        });
    });

    if (allImages.length === 0) {
        showError('Không tìm thấy hình ảnh nào để tải');
        return;
    }

    await performDownload(allImages, 'all');
}

async function performDownload(images, categoryName) {
    const progressEl = document.getElementById('downloadProgress');
    const progressText = document.getElementById('progressText');
    const progressFill = document.getElementById('progressFill');
    const downloadLog = document.getElementById('downloadLog');

    progressEl.classList.remove('hidden');
    downloadLog.innerHTML = '';
    progressFill.style.width = '0%';

    const gameName = (gameConfig.name || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '_');

    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                images,
                gameName,
                categoryName,
            }),
        });

        const data = await res.json();

        if (data.results) {
            let ok = 0, err = 0;
            data.results.forEach((r, i) => {
                const pct = Math.round(((i + 1) / data.results.length) * 100);
                progressFill.style.width = pct + '%';
                progressText.textContent = `${i + 1}/${data.results.length}`;

                if (r.status === 'ok') {
                    ok++;
                    downloadLog.innerHTML += `<div class="ok">✓ ${r.file}</div>`;
                } else {
                    err++;
                    downloadLog.innerHTML += `<div class="err">✗ ${r.file} (${r.code || r.message || 'error'})</div>`;
                }
            });

            downloadLog.innerHTML += `<br><div><strong>Hoàn thành: ${ok} thành công, ${err} lỗi</strong></div>`;
            downloadLog.innerHTML += `<div>📁 Lưu tại: ${data.downloadDir}</div>`;
        }
    } catch (err) {
        downloadLog.innerHTML += `<div class="err">Lỗi: ${err.message}</div>`;
    }

    // Auto-hide after 10s
    setTimeout(() => {
        progressEl.classList.add('hidden');
    }, 10000);
}

function displayRawJson() {
    const viewer = document.getElementById('jsonViewer');
    viewer.textContent = JSON.stringify(gameData, null, 2);
    show('rawJson');
}

function copyJson() {
    const text = document.getElementById('jsonViewer').textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('.raw-json .btn-sm');
        const orig = btn.textContent;
        btn.textContent = '✓ Đã copy!';
        setTimeout(() => btn.textContent = orig, 2000);
    });
}

// Helpers
function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }
function showLoading(v) { v ? show('loading') : hide('loading'); }
function showError(msg) {
    const el = document.getElementById('error');
    el.textContent = '❌ ' + msg;
    el.classList.remove('hidden');
}
function hideError() { document.getElementById('error').classList.add('hidden'); }
