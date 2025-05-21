import eventlet
eventlet.monkey_patch()

import os
import logging
from app import create_app, socketio
from app.telegram_bot import start_bot

def get_local_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logging.warning(f"Не удалось определить IP: {str(e)}")
        return "127.0.0.1"

def main():
    # Настройка логгера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('logs/server.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Конфигурация сервера
    port = int(os.getenv("PORT", 8080))
    local_ip = get_local_ip()
    app = create_app()

    # Запуск Telegram бота
    try:
        start_bot()
        logger.info("Основное приложение: Telegram бот запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска Telegram бота: {e}")

    # Вывод информации о подключении
    print("\n" + "="*50)
    print(f"Локальная сеть: http://{local_ip}:{port}")
    print(f"Локальный адрес: http://localhost:{port}")
    print("="*50 + "\n")

    # Запуск Flask + SocketIO
    try:
        socketio.run(
            app,
            host="0.0.0.0",
            port=port,
            debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true',
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        logging.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()