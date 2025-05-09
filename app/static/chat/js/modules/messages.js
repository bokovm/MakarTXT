import { 
    fetchGet, 
    fetchPost, 
    showToast, 
    showError, 
    scrollToBottom, 
    formatDate,
    escapeHtml,
    escapeAttr
} from '../core/utils.js';

export const Messages = {
    socket: null,
    messageInput: null,
    sendButton: null,
    initialized: false,

    async init(socket) {
        if (this.initialized) return;
        
        try {
            this.socket = socket;
            this.cacheElements();
            this.setupEventListeners();
            await this.load();
            this.setupSocketListeners();
            this.initialized = true;
        } catch (err) {
            console.error('Messages init failed:', err);
            throw err;
        }
    },

    cacheElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-btn');
        
        if (!this.messageInput || !this.sendButton) {
            throw new Error('Required message elements not found');
        }
    },

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyPress(e));
    },

    setupSocketListeners() {
        this.socket?.on('new_message', () => {
            this.load().catch(err => {
                console.error('Failed to load new messages:', err);
            });
        });
    },

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    },

    async load() {
        try {
            const messages = await fetchGet('/api/messages');
            this.renderMessages(messages);
            scrollToBottom(document.getElementById('messages-container'));
        } catch (error) {
            console.error('Ошибка загрузки сообщений:', error);
            showError(error.message.includes('404') 
                ? 'Сервер не отвечает' 
                : 'Ошибка загрузки сообщений');
        }
    },

    renderMessages(messages) {
        const container = document.getElementById('messages-container');
        if (!container) return;

        container.innerHTML = messages.map(msg => `
            <div class="message ${msg.type === 'text' ? 'user' : ''}">
                <div class="message-content">${escapeHtml(msg.content)}</div>
                <span class="message-time">${formatDate(msg.time)}</span>
                <div class="message-actions">
                    <button class="copy-btn" data-content="${escapeAttr(msg.content)}">
                        Копировать
                    </button>
                    ${msg.filename ? `
                    <button class="open-file-btn" 
                            data-filename="${escapeAttr(msg.filename)}">
                        Открыть файл
                    </button>` : ''}
                </div>
            </div>
        `).join('');

        this.setupCopyButtons();
        this.setupOpenFileButtons();
        scrollToBottom(container);
    },

    setupCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(btn.dataset.content);
                    showToast('Текст скопирован!');
                } catch (err) {
                    showError('Ошибка копирования');
                }
            });
        });
    },

    setupOpenFileButtons() {
        document.querySelectorAll('.open-file-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filename = btn.dataset.filename;
                window.open(`/download_file/${encodeURIComponent(filename)}`, '_blank');
            });
        });
    },

    async sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text) return showError('Введите текст сообщения');

        try {
            await fetchPost('/api/save_text', { text });
            this.messageInput.value = '';
            this.socket.emit('new_message');
            showToast('Сообщение отправлено!');
        } catch (error) {
            console.error('Ошибка отправки:', error);
            showError('Ошибка: ' + error.message);
        }
    }
};