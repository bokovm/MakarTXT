// static/chat/js/modules/files.js
import { escapeHtml, escapeAttr } from '../core/utils.js';

import { 
    fetchGet, 
    fetchPost,
    fetchDelete,
    fetchUpload, 
    showToast, 
    showError, 
    formatFileSize,
    showLoader
} from '../core/utils.js';

export const Files = {
    fileToDelete: null,
    socket: null,

    init(socket) {
        this.socket = socket;
        this.setupEventListeners();
        this.load();
        this.setupSocketListeners();
    },

    setupEventListeners() {
        // Загрузка файлов
        const uploadBtn = document.getElementById('upload-btn');
        const fileInput = document.getElementById('file-input');
        const refreshBtn = document.getElementById('refresh-files');
        const confirmDeleteBtn = document.getElementById('confirm-delete');
        const cancelDeleteBtn = document.getElementById('cancel-delete');

        uploadBtn?.addEventListener('click', () => fileInput?.click());
        fileInput?.addEventListener('change', (e) => this.handleFileInput(e));
        refreshBtn?.addEventListener('click', () => this.load());
        confirmDeleteBtn?.addEventListener('click', () => this.confirmDelete());
        cancelDeleteBtn?.addEventListener('click', () => this.cancelDelete());
    },

    setupSocketListeners() {
        if (this.socket) {
            this.socket.on('file_updated', () => this.load());
        }
    },

    async handleFileInput(event) {
        if (event.target.files?.length > 0) {
            await this.uploadFile(event.target.files[0]);
            event.target.value = ''; // Сброс input
        }
    },

    async load() {
        const filesList = document.getElementById('files-list');
        if (!filesList) return;

        const stopLoader = showLoader(filesList);

        try {
            const files = await fetchGet('/get_files');
            this.renderFiles(files);
        } catch (error) {
            console.error('Failed to load files:', error);
            showError('Ошибка загрузки файлов');
        } finally {
            stopLoader();
        }
    },

    renderFiles(files) {
        const filesList = document.getElementById('files-list');
        filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-icon">
                    ${this.getFileIcon(file.name)}
                </div>
                <div class="file-info">
                    <div class="file-name">${this.escapeHtml(file.name)}</div>
                    <div class="file-meta">
                        <span>${formatFileSize(file.size)}</span>
                        <div class="file-actions">
                            <button class="download-btn" data-filename="${this.escapeAttr(file.name)}">
                                <i class="icon-download"></i>
                            </button>
                            <button class="delete-btn" data-filename="${this.escapeAttr(file.name)}">
                                <i class="icon-delete"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            pdf: '📄',
            mp4: '🎥',
            txt: '📝',
            default: '📁'
        };
        return icons[ext] || icons.default;
    },

    setupFileActions() {
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filename = btn.dataset.filename;
                window.location.href = `/download_file/${encodeURIComponent(filename)}`;
            });
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.fileToDelete = btn.dataset.filename;
                document.getElementById('confirm-modal')?.classList.remove('hidden');
            });
        });
    },

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetchUpload('/upload_file', formData);
            showToast('Файл загружен!');
            this.socket?.emit('file_change');
        } catch (error) {
            console.error('Upload error:', error);
            showError('Ошибка загрузки файла');
        }
    },

    async confirmDelete() {
        if (!this.fileToDelete) return;

        try {
            await fetchDelete(`/delete_file/${encodeURIComponent(this.fileToDelete)}`);
            showToast('Файл удален');
            this.socket?.emit('file_change');
            this.load();
        } catch (error) {
            console.error('Delete error:', error);
            showError('Ошибка удаления файла');
        } finally {
            this.cancelDelete();
        }
    },

    cancelDelete() {
        this.fileToDelete = null;
        document.getElementById('confirm-modal')?.classList.add('hidden');
    },

    // Вспомогательные методы безопасности
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    escapeAttr(unsafe) {
        return this.escapeHtml(unsafe).replace(/\//g, "&#x2F;");
    }
};