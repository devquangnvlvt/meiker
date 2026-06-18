const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());
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
        const gameDir = path.join(downloadsDir, f);
        const manifestPath = path.join(gameDir, 'manifest.json');

        let name = `Game ${id}`;
        if (fs.existsSync(manifestPath)) {
            try {
                const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
                if (manifest.name) name = manifest.name;
            } catch (e) { }
        }

        return {
            id,
            folder: f,
            name,
            absolutePath: gameDir
        };
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

// API to scrape a game (starts the python scraper and streams output in real time)
app.post('/api/scrape', (req, res) => {
    const { gameId, customDir } = req.body;
    if (!gameId || !/^\d+$/.test(gameId)) {
        return res.status(400).json({ error: 'Game ID không hợp lệ. Phải là số.' });
    }

    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Transfer-Encoding', 'chunked');

    const { spawn } = require('child_process');
    const scraperScript = path.join(__dirname, 'meiker_scraper.py');

    const args = [scraperScript, gameId];
    if (customDir && customDir.trim() !== '') {
        args.push(customDir.trim());
    }

    // Spawn Python process with unbuffered output (-u)
    const child = spawn('python', ['-u', ...args]);

    child.stdout.on('data', (data) => {
        res.write(data);
    });

    child.stderr.on('data', (data) => {
        res.write(data);
    });

    child.on('close', (code) => {
        if (code === 0) {
            res.write('\n\n--- SUCCESS ---');
        } else {
            res.write(`\n\n--- ERROR: Python scraper exited with code ${code} ---`);
        }
        res.end();
    });

    child.on('error', (err) => {
        res.write(`\n\n--- ERROR: Could not start python scraper. Please check if Python is installed and added to PATH.\nDetails: ${err.message} ---`);
        res.end();
    });
});

// API to open local folder in Windows explorer
app.post('/api/open-folder', (req, res) => {
    const { folderPath } = req.body;
    if (!folderPath) {
        return res.status(400).json({ error: 'Thiếu đường dẫn thư mục.' });
    }

    const absolutePath = path.resolve(folderPath);
    if (!fs.existsSync(absolutePath)) {
        return res.status(404).json({ error: 'Thư mục không tồn tại.' });
    }

    const { exec } = require('child_process');

    exec(`explorer.exe "${absolutePath}"`, (err) => {
        if (err) {
            return res.status(500).json({ error: `Không thể mở thư mục: ${err.message}` });
        }
        res.json({ success: true });
    });
});

// API to get project directory info for default paths
app.get('/api/info', (req, res) => {
    res.json({
        projectRoot: __dirname,
        downloadsDir: path.join(__dirname, 'downloads')
    });
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
