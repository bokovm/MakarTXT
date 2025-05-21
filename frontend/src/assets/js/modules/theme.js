// static/chat/js/modules/theme.js
import { showToast } from '../core/utils.js';

export function initTheme() {
    const themeBtn = document.getElementById('theme-switcher');
    if (!themeBtn) return;

    // Обработчик клика
    themeBtn.addEventListener('click', () => {
        const body = document.body;
        const isDark = body.getAttribute('data-theme') === 'dark';
        const newTheme = isDark ? 'light' : 'dark';
        
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        const icon = themeBtn.querySelector('i');
        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        showToast(`Тема изменена на ${newTheme === 'dark' ? 'тёмную' : 'светлую'}`);
    });

    // Инициализация темы
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    const icon = themeBtn.querySelector('i');
    icon.className = savedTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
}