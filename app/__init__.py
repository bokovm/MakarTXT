import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Инициализация расширений
db = SQLAlchemy()
socketio = SocketIO()
cors = CORS()

def create_app():
    """Фабрика для создания экземпляра Flask приложения"""
    
    # Создание экземпляра приложения
    app = Flask(__name__, static_url_path='/static')
    
    # Конфигурация
    app.config.from_object("app.core.config.Config")
    app.config.update({
        'SEND_FILE_MAX_AGE_DEFAULT': 0,
        'STATIC_FOLDER': 'static',
        'UPLOAD_FOLDER': os.path.join(os.path.expanduser('~'), 'Desktop', 'ReceivedFiles'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })

    # Создание папок
    with app.app_context():  # Создаем контекст приложения
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

    # Инициализация расширений
    db.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    
    # Настройка Socket.IO
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=False
    )

    # Регистрация блюпринтов
    with app.app_context():
        from app.blueprints.chat import chat_bp
        from app.blueprints.youtube.routes import youtube_bp
        
        app.register_blueprint(chat_bp)
        app.register_blueprint(youtube_bp, url_prefix='/youtube')

        # Создание таблиц БД
        db.create_all()

    return app