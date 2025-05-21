// files.js
import { 
  escapeHtml, 
  escapeAttr, 
  fetchGet, 
  fetchPost,
  fetchDelete,
  fetchUpload, 
  showToast, 
  showError, 
  formatFileSize,
  showLoader
} from '../../core/utils.js';

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
            event.target.value = '';
        }
    },

    async load() {
        const filesList = document.getElementById('files-list');
        if (!filesList) return;

        const stopLoader = showLoader(filesList);

        try {
            const files = await fetchGet('/api/files');
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
                    <div class="file-name">${escapeHtml(file.name)}</div>
                    <div class="file-meta">
                        <span>${formatFileSize(file.size)}</span>
                        <div class="file-actions">
                            <button class="download-btn" data-filename="${escapeAttr(file.name)}">
                                <i class="icon-download"></i>
                            </button>
                            <button class="delete-btn" data-filename="${escapeAttr(file.name)}">
                                <i class="icon-delete"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        this.setupFileActions();
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
                window.location.href = `/api/files/download/${encodeURIComponent(filename)}`;
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
            const response = await fetchUpload('/api/files/upload', formData);
            if (response.error) throw new Error(response.error);
            
            showToast('Файл загружен!');
            this.socket?.emit('file_updated');
            this.load();
            
        } catch (error) {
            showError('Ошибка: ' + error.message);
        }
    },

    async confirmDelete() {
        if (!this.fileToDelete) return;

        try {
            await fetchDelete(`/api/files/delete/${encodeURIComponent(this.fileToDelete)}`);
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
    }
};