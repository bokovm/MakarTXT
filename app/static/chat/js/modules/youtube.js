// static/chat/js/modules/youtube.js
import { showToast, showError } from '../core/utils.js';

export const YouTube = {
    currentDownloadId: null,
    progressInterval: null,

    init() {
        const downloadBtn = document.getElementById('youtube-download');
        const urlInput = document.getElementById('youtube-url');
        
        if (downloadBtn && urlInput) {
            downloadBtn.addEventListener('click', () => this.startDownload());
        }
    },

    startDownload() {
        const url = document.getElementById('youtube-url').value.trim();
        if (!this.validateUrl(url)) return;

        this.showProgressUI();
        
        fetch('/youtube/download/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            if(data.download_id) {
                this.currentDownloadId = data.download_id;
                this.monitorProgress();
                showToast('Загрузка начата. Можно закрыть страницу');
            }
        })
        .catch(error => {
            showError('Ошибка запуска загрузки');
            this.resetUI();
        });
    },

    validateUrl(url) {
        const ytRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}/i;
        if (!ytRegex.test(url)) {
            showError('Некорректная ссылка YouTube');
            return false;
        }
        return true;
    },

    showProgressUI() {
        document.getElementById('download-progress').classList.remove('hidden');
        document.getElementById('youtube-download').disabled = true;
    },

    monitorProgress() {
        this.progressInterval = setInterval(() => {
            if (!this.currentDownloadId) return;
            
            fetch(`/youtube/download/status/${this.currentDownloadId}`)
            .then(response => response.json())
            .then(data => {
                if(data.status === 'completed') {
                    this.handleComplete(data);
                } else if(data.status === 'error') {
                    this.handleError(data.message);
                } else if(data.progress) {
                    this.updateProgress(data.progress);
                }
            });
        }, 2000);
    },

    updateProgress(percent) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const numericPercent = parseFloat(percent); // Конвертировать в число
        
        if (progressBar) {
            progressBar.style.width = `${numericPercent}%`;
            progressBar.textContent = `${numericPercent.toFixed(1)}%`;
        }
    },

    handleComplete(data) {
        clearInterval(this.progressInterval);
        this.showDownloadLink(data.url, data.title);
        this.resetUI();
    },

    handleError(message) {
        clearInterval(this.progressInterval);
        showError(message || 'Ошибка загрузки');
        this.resetUI();
    },

    showDownloadLink(url, title) {
        const linkContainer = document.getElementById('download-link');
        linkContainer.innerHTML = `
            <a href="${url}" class="download-link" download>
                Скачать "${title}"
            </a>
        `;
    },

    resetUI() {
        document.getElementById('youtube-download').disabled = false;
        document.getElementById('youtube-url').value = '';
        this.currentDownloadId = null;
    }
};