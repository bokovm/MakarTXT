// app\static\chat\js\main.js

import { Messages } from './modules/messages.js';
import { Files } from './modules/files.js';
import { YouTube } from './modules/youtube.js';
import { History } from './modules/history.js';
import { setupSocketHandlers } from './core/socket.js';
import { showToast, showError } from './core/utils.js';
import { io } from 'https://cdn.socket.io/4.7.4/socket.io.esm.min.js';

class App {
    constructor() {
        this.socket = null;
        this.closeModal = this.closeModal.bind(this);
        this.handleFileUpload = this.handleFileUpload.bind(this);
    }

    async init() {
        try {
            this.socket = io();
            this.initModals();
            this.initSocket();
            await this.initModules();
            this.setupGlobalListeners();
            this.setupPanelSwitcher();
        } catch (err) {
            console.error('App initialization error:', err);
            showError('Ошибка инициализации приложения');
        }
    }

    initModals() {
        // Обработчики модальных окон
        document.querySelectorAll('.modal-backdrop, .close-btn').forEach(el => {
            el.addEventListener('click', this.closeModal);
        });

        // Обработчик кнопки истории
        document.getElementById('show-history')?.addEventListener('click', () => {
            History.load();
            document.getElementById('history-modal').classList.remove('hidden');
            document.body.classList.add('modal-open');
        });

        document.getElementById('upload-btn')?.addEventListener('click', () => {
            document.getElementById('upload-modal').classList.remove('hidden');
            document.body.classList.add('modal-open');
        });

        document.getElementById('file-input')?.addEventListener('change', this.handleFileUpload);

        // Блокировка закрытия при клике на контент
        document.querySelectorAll('.modal-content').forEach(content => {
            content.addEventListener('click', (e) => e.stopPropagation());
        });
    }

    handleFileUpload(event) {
        Files.handleFileInput(event);
        this.closeModal();
    }

    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.classList.remove('modal-open');
    }

    initSocket() {
        this.socket.on('connect', () => {
            showToast('Соединение установлено');
        });
    
        this.socket.on('connect_error', (err) => {
            console.error('Socket connection error:', err);
            showError('Ошибка соединения с сервером');
        });

        setupSocketHandlers(this.socket);
    }

    setupSocketHandlers() {
        this.socket.on('file_updated', () => {
            Messages.load();
            Files.load();
        });
        
        this.socket.on('new_message', () => {
            Messages.load();
        });
    }

    setupPanelSwitcher() {
        const switchPanel = (panel) => {
            ['history', 'files'].forEach(name => {
                const element = document.getElementById(`${name}-panel`);
                const button = document.getElementById(`${name}-btn`);
                if (element && button) {
                    element.classList.toggle('hidden', name !== panel);
                    button.classList.toggle('active', name === panel);
                }
            });
            
            panel === 'history' ? Messages.load() : Files.load();
        };

        document.getElementById('history-btn')?.addEventListener('click', () => switchPanel('history'));
        document.getElementById('files-btn')?.addEventListener('click', () => switchPanel('files'));
    }

    async initModules() {
        try {
            await Messages.init(this.socket);
            await Files.init(this.socket);
            YouTube.init();
        } catch (err) {
            console.error('Module init error:', err);
            showError('Ошибка инициализации модулей');
            throw err;
        }
    }

    setupGlobalListeners() {
        window.addEventListener('error', (e) => {
            console.error('Global error:', e);
            showError(`Ошибка: ${e.message}`);
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled rejection:', e.reason);
            showError(`Необработанная ошибка: ${e.reason}`);
        });

        // Автоматическая высота текстового поля
        const textArea = document.getElementById('message-input');
        if (textArea) {
            textArea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = `${this.scrollHeight}px`;
            });
        }
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    new App().init().catch(err => {
        console.error('Application failed to start:', err);
        showError('Критическая ошибка при запуске');
    });
});