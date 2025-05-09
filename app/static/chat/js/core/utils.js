// static/chat/js/core/utils.js

/**
 * HTTP-методы
 */
export async function fetchGet(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('GET Error:', error);
        throw error;
    }
}

export async function fetchPost(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('POST Error:', error);
        throw error;
    }
}

export async function fetchDelete(url) {
    try {
        const response = await fetch(url, { method: 'DELETE' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('DELETE Error:', error);
        throw error;
    }
}

export async function fetchUpload(url, formData) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Upload Error:', error);
        throw error;
    }
}

/**
 * Уведомления
 */
export function showToast(message, type = 'success', duration = 3000) {
    const container = getToastContainer();
    const toast = createToastElement(message, type);
    
    container.appendChild(toast);
    setupToastAutoDismiss(toast, duration);
    setupToastClickHandler(toast);
}

export function showError(message) {
    showToast(message, 'error', 5000);
}

function getToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        Object.assign(container.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: '1000'
        });
        document.body.appendChild(container);
    }
    return container;
}

function createToastElement(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    const typeStyles = {
        success: { background: '#4CAF50', color: 'white' },
        error: { background: '#F44336', color: 'white' },
        warning: { background: '#FF9800', color: 'black' }
    };

    Object.assign(toast.style, {
        padding: '12px 24px',
        borderRadius: '4px',
        marginBottom: '10px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
        animation: 'fadeIn 0.3s ease-out',
        ...typeStyles[type]
    });

    return toast;
}

function setupToastAutoDismiss(toast, duration) {
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function setupToastClickHandler(toast) {
    toast.addEventListener('click', () => {
        toast.style.animation = 'fadeOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    });
}

/**
 * Форматирование данных
 */
export function formatFileSize(bytes) {
    if (typeof bytes !== 'number') return '0 B';
    
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function formatDate(date) {
    try {
        const d = new Date(date);
        return d.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch {
        return '';
    }
}

/**
 * Безопасность
 */
export function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

export function escapeAttr(unsafe) {
    return escapeHtml(unsafe).replace(/\//g, "&#x2F;");
}

/**
 * DOM-утилиты
 */
export function scrollToBottom(element) {
    if (!element) return;
    element.scrollTop = element.scrollHeight;
}

export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Текст скопирован!');
        return true;
    } catch (err) {
        console.error('Copy failed:', err);
        showError('Не удалось скопировать текст');
        return false;
    }
}

export function showLoader(element) {
    if (!element) return () => {};
    
    const loader = document.createElement('div');
    loader.className = 'loader';
    loader.innerHTML = `
        <div class="spinner"></div>
        <div class="loading-text">Загрузка...</div>
    `;
    
    element.style.position = 'relative';
    element.appendChild(loader);

    return () => {
        try {
            loader.remove();
        } catch (e) {
            console.error('Loader remove error:', e);
        }
    };
}

/**
 * Валидация
 */
export function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch {
        return false;
    }
}

/**
 * Инициализация стилей
 */
function injectGlobalStyles() {
    if (document.getElementById('utils-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'utils-styles';
    style.textContent = `
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
        .fade-in { animation: fadeIn 0.3s ease-out; }
        .fade-out { animation: fadeOut 0.3s ease-in; }
        .loader {
            position: absolute;
            inset: 0;
            background: rgba(255,255,255,0.8);
            display: grid;
            place-items: center;
            z-index: 100;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(0,0,0,0.1);
            border-radius: 50%;
            border-left-color: var(--primary);
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
}

// Инициализируем стили при загрузке
injectGlobalStyles();