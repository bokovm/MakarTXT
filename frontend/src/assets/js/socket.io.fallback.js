// app\static\chat\js\socket.io.fallback.js

(() => {
    console.error('Failed to load Socket.io from CDN, loading local version');
    
    // Создаем элемент script динамически
    const script = document.createElement('script');
    script.src = '/static/chat/js/socket.io.min.js';
    script.integrity = 'sha384-...'; // Добавьте хеш целостности если используете SRI
    script.crossOrigin = 'anonymous';
    
    // Обработка успешной загрузки
    script.onload = () => {
        console.log('Local Socket.io loaded successfully');
        if (typeof io !== 'undefined') {
            window.dispatchEvent(new Event('socketio-loaded'));
        }
    };
    
    // Обработка ошибок
    script.onerror = () => {
        console.error('Failed to load local Socket.io');
        showError('Критическая ошибка: не удалось загрузить библиотеку связи');
    };
    
    document.head.appendChild(script);
})();