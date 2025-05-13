import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логгера
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'app.log'),
        logging.StreamHandler()
    ]
)

class Config:
    # Основные настройки
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SOCKETIO_ASYNC_MODE = 'eventlet'
    JWT_EXP_HOURS = 24

    # Пути
    BASE_DIR = Path(__file__).parent.parent
    TEMPLATES_FOLDER = BASE_DIR / 'app' / 'templates'
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'backend' / 'uploads'))
    YT_DOWNLOAD_FOLDER = BASE_DIR / 'backend' / 'youtube_downloads'
    LOGS_DIR = BASE_DIR / 'logs'
    INSTANCE_DIR = BASE_DIR / 'instance'
    
    # База данных
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR}/backend/instance/app.db"

    # Лимиты
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'webp', 'tgs'}

    # RapidAPI
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
    RAPIDAPI_HOST = "youtube138.p.rapidapi.com"

    # Настройки yt-dlp
    YDL_OPTS = {
        'proxy': os.getenv('PROXY_URL'),  # Пример: socks5://user:pass@host:port
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'socket_timeout': 45,
        'retries': 5,
        'fragment_retries': 5,
        'skip_unavailable_fragments': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android_embedded'],
                'skip': ['dash', 'hls']
            }
        },
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }]
    }

    @classmethod
    def init_app(cls, app):
        """Инициализация приложения"""
        # Создание обязательных директорий
        required_dirs = [
            cls.UPLOAD_FOLDER,
            cls.YT_DOWNLOAD_FOLDER,
            cls.LOGS_DIR,
            cls.INSTANCE_DIR
        ]
        
        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    YDL_OPTS = {
        **Config.YDL_OPTS,
        'verbose': True,
        'dumpjson': True,
        'progress_hooks': [lambda d: print(f"Прогресс: {d.get('_percent_str', '?')}")]
    }

class ProductionConfig(Config):
    """Конфигурация для продакшена""" 
    DEBUG = False
    PROPAGATE_EXCEPTIONS = True
    YDL_OPTS = {
        **Config.YDL_OPTS,
        'quiet': True,
        'no_warnings': True
    }

def get_config():
    """Фабрика конфигураций"""
    env = os.getenv('FLASK_ENV', 'development').lower()
    return {
        'development': DevelopmentConfig,
        'production': ProductionConfig
    }.get(env, DevelopmentConfig)

# Инициализация конфига
app_config = get_config()()