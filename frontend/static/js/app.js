// API endpoint base URL
const API_BASE = '/api';

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const ragToggle = document.getElementById('rag-toggle');
const docCount = document.getElementById('doc-count');
const statusElement = document.getElementById('status');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    updateDocumentCount();

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        userInput.focus();
    }
});

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (!statusElement) return;

        if (data.status === 'healthy') {
            statusElement.textContent = 'Online';
            statusElement.className = 'healthy';
        } else {
            statusElement.textContent = 'Error';
            statusElement.className = 'error';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        if (statusElement) {
            statusElement.textContent = 'Offline';
            statusElement.className = 'error';
        }
    }
}

// Update document count
async function updateDocumentCount() {
    try {
        const response = await fetch(`${API_BASE}/documents/count`);
        const data = await response.json();
        if (docCount) {
            docCount.textContent = data.count ?? 0;
        }
    } catch (error) {
        console.error('Failed to get document count:', error);
        if (docCount) {
            docCount.textContent = '0';
        }
    }
}

// Send chat message
async function sendMessage() {
    if (!userInput) return;

    const message = userInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    if (userInput) {
        userInput.value = '';
    }

    // Disable send button
    if (sendBtn) {
        sendBtn.disabled = true;
    }

    // Show loading indicator
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                use_rag: ragToggle ? ragToggle.checked : true
            })
        });

        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }

        const data = await response.json();

        // Remove loading indicator
        removeLoadingMessage(loadingId);

        const reply = data?.response || 'No response returned.';
        addMessage(reply, 'bot', data?.sources);

    } catch (error) {
        console.error('Error sending message:', error);
        removeLoadingMessage(loadingId);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    } finally {
        if (sendBtn) {
            sendBtn.disabled = false;
        }
        if (userInput) {
            userInput.focus();
        }
    }
}

// Simple markdown parser
function parseMarkdown(text) {
    // Convert markdown to HTML
    let html = text;

    // Headers (## and ###)
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

    // Bold text (**text**)
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Bullet lists (- item or • item)
    html = html.replace(/^[•\-]\s+(.+)$/gm, '<li>$1</li>');

    // Wrap consecutive <li> in <ul>
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Preserve line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(<[uh][123l]>)/g, '$1');
    html = html.replace(/(<\/[uh][123l]>)<\/p>/g, '$1');

    return html;
}

// Add message to chat
function addMessage(text, sender, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const senderLabel = document.createElement('strong');
    senderLabel.textContent = sender === 'user' ? 'You:' : 'MPP Expert:';

    const messageText = document.createElement('div');

    // Parse markdown for bot messages, plain text for user
    if (sender === 'bot') {
        messageText.innerHTML = parseMarkdown(text);
    } else {
        const p = document.createElement('p');
        p.textContent = text;
        messageText.appendChild(p);
    }

    contentDiv.appendChild(senderLabel);
    contentDiv.appendChild(messageText);

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';

        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'sources-title';
        sourcesTitle.textContent = 'Sources:';
        sourcesDiv.appendChild(sourcesTitle);

        sources.forEach((source, index) => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';
            const sourceLabel = source?.source || 'Document';
            const chunkLabel = source?.chunk !== undefined ? ` (chunk ${source.chunk})` : '';
            sourceItem.textContent = `${index + 1}. ${sourceLabel}${chunkLabel}`;

            if (source?.text) {
                const snippet = document.createElement('span');
                snippet.className = 'source-snippet';
                const trimmed = source.text.trim();
                snippet.textContent = trimmed.length > 160 ? `${trimmed.slice(0, 160)}...` : trimmed;
                sourceItem.appendChild(snippet);
            }

            sourcesDiv.appendChild(sourceItem);
        });

        contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add loading message
function addLoadingMessage() {
    const loadingId = `loading-${Date.now()}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = loadingId;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const senderLabel = document.createElement('strong');
    senderLabel.textContent = 'MPP Expert:';

    const statusText = document.createElement('p');
    statusText.style.cssText = 'margin: 10px 0; color: var(--accent);';
    statusText.textContent = 'Verifying accuracy';

    const loadingDiv = document.createElement('div');
    loadingDiv.style.cssText = 'display: flex; gap: 5px; margin-top: 10px;';
    loadingDiv.innerHTML = `
        <span class="loading"></span>
        <span class="loading"></span>
        <span class="loading"></span>
    `;

    contentDiv.appendChild(senderLabel);
    contentDiv.appendChild(statusText);
    contentDiv.appendChild(loadingDiv);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    return loadingId;
}

// Remove loading message
function removeLoadingMessage(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}
