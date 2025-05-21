// history.js
import { 
    fetchGet, 
    showToast, 
    showError, 
    formatDate,
    escapeHtml,
    escapeAttr 
} from '../../core/utils.js';

export const History = {
    async load() {
        try {
            const response = await fetchGet('/api/history');
            
            if (response.error) {
                throw new Error(response.error);
            }
            
            if (!Array.isArray(response)) {
                throw new Error('Некорректный формат ответа сервера');
            }

            this.render(response);
            
        } catch (error) {
            showError('Ошибка загрузки истории: ' + error.message);
            console.error('History load error:', error);
        }
    },

    render(records) {
        const container = document.querySelector('.history-list');
        if (!container) return;
    
        if (!records || !records.length) {
        container.innerHTML = '<div class="empty-state">Нет записей</div>';
        return;
    }
      
        container.innerHTML = records.map(record => `
          <div class="history-item">
            <div class="file-header">
              <span class="filename" title="${escapeAttr(record.filename)}">
                ${escapeHtml(record.filename)}
              </span>
              <div class="item-actions">
                <button class="action-btn copy-btn" aria-label="Копировать">
                  <svg><use href="#copy-icon"/></svg>
                </button>
                <button class="action-btn download-btn" aria-label="Скачать">
                  <svg><use href="#download-icon"/></svg>
                </button>
              </div>
            </div>
            <pre class="item-text">${escapeHtml(record.content)}</pre>
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
                    showToast('Текст скопирован!');
                });
            });
        });

        // Скачивание
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filename = btn.closest('.history-item').dataset.filename;
                window.open(`/download_file/${encodeURIComponent(filename)}`, '_blank');
            });
        });
    }
};