import eventlet
eventlet.monkey_patch()
Queue=True
import os
import logging
from app import create_app, socketio
from app.telegram_bot import start_bot, stop_bot

# Инициализация приложения и логгера на верхнем уровне
app = create_app()
logger = logging.getLogger(__name__)

def configure_logging():
    """Настройка системы логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('logs/server.log'),
            logging.StreamHandler()
        ]
    )
    logger.info("Логгирование успешно настроено")

def get_server_info():
    """Получение информации о сервере"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return {
            "local_ip": local_ip,
            "port": int(os.getenv("PORT", 8080)),
            "debug": os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        }
    except Exception as e:
        logger.warning(f"Не удалось определить IP: {str(e)}")
        return {
            "local_ip": "127.0.0.1",
            "port": 8080,
            "debug": False
        }

def run_server():
    """Запуск сервера и дополнительных сервисов"""
    try:
        # Запуск Telegram бота
        start_bot()
        logger.info("Telegram бот успешно запущен")

        # Получение параметров сервера
        server_info = get_server_info()
        
        # Вывод информации о сервере
        logger.info("\n" + "="*50)
        logger.info(f"Локальная сеть: http://{server_info['local_ip']}:{server_info['port']}")
        logger.info(f"Локальный адрес: http://localhost:{server_info['port']}")
        logger.info("="*50 + "\n")

        # Запуск SocketIO сервера
        socketio.run(
            app,
            host="0.0.0.0",
            port=server_info['port'],
            debug=server_info['debug'],
            use_reloader=False,
            log_output=True
        )

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        stop_bot()
        raise
    finally:
        stop_bot()

if __name__ == "__main__":
    configure_logging()
    run_server()
else:
    # Инициализация для Gunicorn
    configure_logging()
    start_bot()
    logger.info("Приложение инициализировано в режиме WSGI")