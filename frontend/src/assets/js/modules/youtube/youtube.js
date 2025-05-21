import { 
  showToast, 
  showError, 
  formatFileSize 
} from '../../core/utils.js';
import { Files } from '../chat/files.js';

export const YouTube = {
    selectors: {
        urlInput: '#youtube-url',
        downloadBtn: '#youtube-download',
        formatSelect: '#format-select',
        progressBar: '#yt-progress-bar',
        progressText: '#yt-progress-text',
        thumbnail: '#yt-thumbnail',
        videoTitle: '#yt-video-title',
        duration: '#yt-duration'
    },

    init() {
        this.cacheElements();
        this.setupEventListeners();
    },

    cacheElements() {
        this.elements = {};
        for (const [key, selector] of Object.entries(this.selectors)) {
            this.elements[key] = document.querySelector(selector);
        }
    },

    setupEventListeners() {
        this.elements.downloadBtn?.addEventListener('click', () => this.downloadVideo());
        this.elements.urlInput?.addEventListener('input', () => this.handleUrlInput());
    },

    async handleUrlInput() {
        const url = this.elements.urlInput.value.trim();
        if (!this.validateUrl(url)) return;

        try {
            const videoInfo = await this.fetchVideoInfo(url);
            this.updateVideoInfo(videoInfo);
        } catch (error) {
            this.clearVideoInfo();
            showError('Не удалось получить информацию о видео');
        }
    },

    async fetchVideoInfo(url) {
        try {
            const response = await fetch(`/api/youtube/info?url=${encodeURIComponent(url)}`);
            if (!response.ok) throw new Error('HTTP error');
            return await response.json();
        } catch (error) {
            console.error('YouTube API Error:', error);
            throw error;
        }
    },

    updateVideoInfo(data) {
        if (!data.title) throw new Error('Invalid video data');

        this.elements.thumbnail.src = data.thumbnail;
        this.elements.videoTitle.textContent = data.title;
        this.elements.duration.textContent = this.formatDuration(data.duration);

        this.elements.formatSelect.innerHTML = data.formats
            .map(format => `
                <option value="${format.format_id}">
                    ${format.resolution} (${format.ext.toUpperCase()}) • 
                    ${format.filesize ? formatFileSize(format.filesize) : 'N/A'}
                </option>
            `).join('');

        this.toggleUIElements(true);
    },

    async downloadVideo() {
        const url = this.elements.urlInput.value.trim();
        const formatId = this.elements.formatSelect.value;

        if (!this.validateUrl(url)) {
            showError('Пожалуйста, введите корректную ссылку YouTube');
            return;
        }

        try {
            this.toggleLoadingState(true);
            
            const response = await fetch('/api/youtube/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, format: formatId })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error);
            }

            const { filename, title, download_url } = await response.json();
            this.handleDownloadSuccess(filename, download_url);
            showToast(`Видео "${title}" успешно загружено!`);
        } catch (error) {
            showError(error.message);
        } finally {
            this.toggleLoadingState(false);
        }
    },

    handleDownloadSuccess(filename, downloadUrl) {
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        Files.load().catch(console.error);
    },

    validateUrl(url) {
        const patterns = [
            /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)/i,
            /^(https?:\/\/)?(music\.youtube\.com\/watch\?v=)/i
        ];
        return patterns.some(regex => regex.test(url));
    },

    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor(seconds % 3600 / 60);
        const s = Math.floor(seconds % 60);
        return [h, m, s]
            .map(v => v.toString().padStart(2, '0'))
            .filter((v, i) => v !== '00' || i > 0)
            .join(':');
    },

    toggleLoadingState(isLoading) {
        this.elements.downloadBtn.disabled = isLoading;
        this.elements.downloadBtn.innerHTML = isLoading
            ? '<div class="spinner"></div> Загрузка...'
            : '<i class="fas fa-download"></i> Скачать';
    },

    toggleUIElements(show) {
        [this.elements.formatSelect, this.elements.thumbnail, 
         this.elements.videoTitle, this.elements.duration].forEach(el => {
            if (el) el.style.display = show ? 'block' : 'none';
        });
    },

    clearVideoInfo() {
        this.elements.thumbnail.src = '';
        this.elements.videoTitle.textContent = '';
        this.elements.duration.textContent = '';
        this.elements.formatSelect.innerHTML = '';
        this.toggleUIElements(false);
    }
};