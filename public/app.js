// Start Scrape game by calling Node backend
async function startScrape() {
    const gameIdInput = document.getElementById('gameId');
    const savePathInput = document.getElementById('savePath');
    const btnStart = document.getElementById('btnStartDownload');
    
    const gameId = gameIdInput.value.trim();
    if (!gameId) {
        alert('Vui lòng nhập Game ID trước khi tải!');
        gameIdInput.focus();
        return;
    }
    if (!/^\d+$/.test(gameId)) {
        alert('Game ID chỉ bao gồm chữ số!');
        gameIdInput.focus();
        return;
    }

    // Set target custom path if not empty
    const customDir = savePathInput.value.trim();

    // Prepare UI
    btnStart.disabled = true;
    btnStart.innerHTML = `<span class="spinner" style="width:16px;height:16px;margin:0;display:inline-block;vertical-align:middle;border-width:2px;"></span> Đang tải...`;
    
    const termSection = document.getElementById('terminalSection');
    termSection.classList.remove('hidden');
    
    const logOutput = document.getElementById('logOutput');
    logOutput.textContent = `[INIT] Bắt đầu gửi yêu cầu tải game ID: ${gameId}...\n`;
    
    const statusBadge = document.getElementById('statusBadge');
    statusBadge.textContent = 'Đang tải';
    statusBadge.className = 'status-running';

    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ gameId, customDir })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `Lỗi HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        // Scroll terminal to bottom helper
        const scrollToBottom = () => {
            const body = document.querySelector('.terminal-body');
            body.scrollTop = body.scrollHeight;
        };

        // Read the stream
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            
            // Reformat progress carriage returns if they exist so it displays nicely on the terminal
            const formattedText = text.replace(/\r/g, '\n');
            
            logOutput.textContent += formattedText;
            scrollToBottom();
        }

        // Check result
        const finalLog = logOutput.textContent;
        if (finalLog.includes('--- SUCCESS ---')) {
            statusBadge.textContent = 'Thành công';
            statusBadge.className = 'status-success';
        } else if (finalLog.includes('--- ERROR:')) {
            statusBadge.textContent = 'Lỗi';
            statusBadge.className = 'status-error';
        } else {
            statusBadge.textContent = 'Đã xong';
            statusBadge.className = 'status-success';
        }

    } catch (err) {
        logOutput.textContent += `\n[LỖI HỆ THỐNG] ${err.message}\n`;
        statusBadge.textContent = 'Lỗi';
        statusBadge.className = 'status-error';
    } finally {
        btnStart.disabled = false;
        btnStart.innerHTML = `<span class="btn-icon">⚡</span> Bắt đầu Tải xuống`;
    }
}

// Copy Console logs to clipboard
function copyConsoleLogs() {
    const logOutput = document.getElementById('logOutput');
    navigator.clipboard.writeText(logOutput.textContent)
        .then(() => alert('Đã sao chép toàn bộ log vào bộ nhớ tạm!'))
        .catch(err => alert('Không thể sao chép: ' + err));
}

// Clear console logs
function clearConsoleLogs() {
    document.getElementById('logOutput').textContent = 'Sẵn sàng tải game. Nhấp "Bắt đầu Tải xuống" để bắt đầu...';
    const statusBadge = document.getElementById('statusBadge');
    statusBadge.textContent = 'Đang chờ';
    statusBadge.className = 'status-ready';
}
