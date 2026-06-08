const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/downloads', express.static(path.join(__dirname, 'downloads')));

// API to list downloaded games
app.get('/api/games', (req, res) => {
    const downloadsDir = path.join(__dirname, 'downloads');
    if (!fs.existsSync(downloadsDir)) {
        return res.json([]);
    }
    const games = fs.readdirSync(downloadsDir).filter(f => 
        fs.statSync(path.join(downloadsDir, f)).isDirectory() && f.startsWith('meiker_')
    ).map(f => {
        const id = f.replace('meiker_', '');
        return { id, folder: f };
    });
    res.json(games);
});

// API to load specific game raw_data.json
app.get('/api/game_data/:id', (req, res) => {
    const gameId = req.params.id;
    const dataPath = path.join(__dirname, 'downloads', `meiker_${gameId}`, 'raw_data.json');
    if (!fs.existsSync(dataPath)) {
        return res.status(404).json({ error: 'Data not found. Please scrape the game first.' });
    }
    const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    res.json(data);
});

// Image proxy to bypass CORS for canvas.toDataURL() export
app.get('/api/proxy', async (req, res) => {
    const targetUrl = req.query.url;
    if (!targetUrl || !targetUrl.startsWith('https://cdn.meiker.io/')) {
        return res.status(400).json({ error: 'Invalid or disallowed URL' });
    }
    try {
        const https = require('https');
        https.get(targetUrl, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (imgRes) => {
            res.set('Content-Type', imgRes.headers['content-type'] || 'image/png');
            res.set('Cache-Control', 'public, max-age=86400');
            imgRes.pipe(res);
        }).on('error', () => res.status(500).json({ error: 'Proxy fetch failed' }));
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Open character creator: http://localhost:${PORT}/creator.html`);
    console.log(`Serving static files from /public and /downloads`);
});
