// messages.js
import { 
    fetchGet, 
    fetchPost, 
    showToast, 
    showError, 
    scrollToBottom, 
    formatDate,
    escapeHtml,
    escapeAttr,
    showLoader,
    hideLoader 
} from '../../core/utils.js';

export const Messages = {
    socket: null,
    messageInput: null,
    sendButton: null,
    initialized: false,

    async init(socket) {
        if (this.initialized) return;
        
        try {
            this.socket = socket;
            await this.cacheElements();
            this.setupEventListeners();
            await this.load();
            this.setupSocketListeners();
            this.initialized = true;
        } catch (err) {
            console.error('Messages init failed:', err);
            throw err;
        }
    },

    async cacheElements() {
        const waitForElement = (id, timeout = 5000) => {
            return new Promise((resolve) => {
                let attempts = 0;
                const check = () => {
                    const el = document.getElementById(id);
                    if (el) return resolve(el);
                    if (attempts++ < 10) setTimeout(check, timeout/10);
                };
                check();
            });
        };

        this.messageInput = await waitForElement('message-input');
        this.sendButton = await waitForElement('send-btn');
    },

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    },

    setupSocketListeners() {
        this.socket?.on('new_message', () => {
            this.load().catch(err => console.error('Ошибка загрузки сообщений:', err));
        });
    },

    async load() {
        try {
            const stopLoader = showLoader(document.getElementById('messages-container'));
            const messages = await fetchGet('/api/messages');
            this.renderMessages(messages);
        } catch (error) {
            console.error('Ошибка загрузки сообщений:', error);
            showError(error.message || 'Ошибка соединения');
        } finally {
            hideLoader(document.getElementById('messages-container'));
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
                    <button class="open-file-btn" data-filename="${escapeAttr(msg.filename)}">
                        Открыть файл
                    </button>` : ''}
                </div>
            </div>
        `).join('');

        this.setupCopyButtons();
        this.setupOpenFileButtons();
    },

    setupCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                navigator.clipboard.writeText(btn.dataset.content)
                    .then(() => showToast('Скопировано!'))
                    .catch(() => showError('Ошибка копирования'));
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
        if (!text) return showError('Введите сообщение');
        
        try {
            await fetchPost('/api/save_text', { text });
            this.messageInput.value = '';
            this.socket.emit('new_message');
            scrollToBottom(document.getElementById('messages-container'));
            showToast('Сообщение отправлено!');
        } catch (error) {
            showError(error.message)
            showError('Ошибка отправки');
        }
    }
};