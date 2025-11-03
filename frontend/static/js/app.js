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

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            statusElement.textContent = 'Online';
            statusElement.className = 'healthy';
        } else {
            statusElement.textContent = 'Error';
            statusElement.className = 'error';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        statusElement.textContent = 'Offline';
        statusElement.className = 'error';
    }
}

// Update document count
async function updateDocumentCount() {
    try {
        const response = await fetch(`${API_BASE}/documents/count`);
        const data = await response.json();
        docCount.textContent = data.count;
    } catch (error) {
        console.error('Failed to get document count:', error);
    }
}

// Send chat message
async function sendMessage() {
    const message = userInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    userInput.value = '';

    // Disable send button
    sendBtn.disabled = true;

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
                use_rag: ragToggle.checked
            })
        });

        const data = await response.json();

        // Remove loading indicator
        removeLoadingMessage(loadingId);

        // Add bot response
        addMessage(data.response, 'bot', data.sources);

    } catch (error) {
        console.error('Error sending message:', error);
        removeLoadingMessage(loadingId);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Add message to chat
function addMessage(text, sender, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const senderLabel = document.createElement('strong');
    senderLabel.textContent = sender === 'user' ? 'You:' : 'MPP Expert:';

    const messageText = document.createElement('p');
    messageText.textContent = text;

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
            sourceItem.textContent = `${index + 1}. ${source.source}`;
            sourcesDiv.appendChild(sourceItem);
        });

        contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add loading message with dual-pass verification steps
function addLoadingMessage() {
    const loadingId = `loading-${Date.now()}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = loadingId;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const senderLabel = document.createElement('strong');
    senderLabel.textContent = 'MPP Expert (Dual-Pass AI Verification):';

    const statusText = document.createElement('p');
    statusText.style.cssText = 'margin: 10px 0; color: var(--accent);';
    statusText.innerHTML = `
        <strong>🤖 Verification in Progress...</strong><br><br>
        Pass 1: Grok 4 analyzing with exact quotes...<br>
        Pass 1: Gemini verifying accuracy and citations...<br>
        Pass 2: Grok 4 reviewing Pass 1 results...<br>
        Pass 2: Gemini final verification...
    `;

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
