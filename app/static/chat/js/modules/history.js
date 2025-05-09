// static/chat/js/modules/history.js (новый модуль)
import { 
    fetchGet, 
    showToast, 
    showError, 
    formatDate,
    escapeHtml,
    escapeAttr 
} from '../core/utils.js';

export const History = {
    async load() {
        try {
            const response = await fetchGet('/api/history');
            if (response.error) throw new Error(response.error);
            
            // Сортируем по дате (новые сверху)
            const sorted = response.sort((a, b) => b.timestamp - a.timestamp);
            this.render(sorted);
            
        } catch (error) {
            showError('Ошибка загрузки истории: ' + error.message);
        }
    },

    render(records) {
        const container = document.querySelector('.history-list');
        if (!container) return;

        container.innerHTML = records.map(record => `
            <div class="history-item">
                <!-- Текст сообщения -->
                <div class="item-text">${escapeHtml(record.content)}</div>
                
                <!-- Кнопки действий -->
                <div class="item-actions">
                    <button class="btn-icon copy-btn" title="Копировать">
                        <svg width="18" height="18" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12V1Z"/>
                        </svg>
                    </button>
                    <button class="btn-icon download-btn" title="Скачать">
                        <svg width="18" height="18" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7l7-7z"/>
                        </svg>
                    </button>
                </div>

                <!-- Мета-данные -->
                <div class="item-meta">
                    <span class="filename">${escapeHtml(record.filename)}</span>
                    <span>${formatFileSize(record.size)}</span>
                </div>
            </div>
        `).join('');

        this.setupActions();
    },

    setupActions() {
        // Копирование
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.closest('.history-item').querySelector('.item-text').textContent;
                navigator.clipboard.writeText(text).then(() => {
                    showToast('Текст скопирован в буфер');
                });
            });
        });

        // Скачивание
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filename = btn.closest('.history-item').querySelector('.filename').textContent;
                window.open(`/download_file/${encodeURIComponent(filename)}`, '_blank');
            });
        });
    }
};