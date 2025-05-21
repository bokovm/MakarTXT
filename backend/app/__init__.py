from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import logging

# Инициализация расширений
socketio = SocketIO()
cors = CORS()

def create_app():
    # Загрузка .env файла
    load_dotenv(os.path.join(
        os.path.dirname(__file__), 
        '../../.env'
    ))

    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        UPLOAD_FOLDER=os.path.abspath(os.getenv('UPLOAD_FOLDER', 'uploads')),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///db.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Инициализация CORS
    cors.init_app(
        app,
        resources={
            r"/api/*": {"origins": "*"},
            r"/socket.io/*": {"origins": "*"}
        }
    )
    
    # Регистрация сервисов (ИСПРАВЛЕННЫЙ ИМПОРТ)
    from .services import FileService
    FileService.init_app(app)

    # Регистрация API
    from .routes.api import bp as api_bp
    app.register_blueprint(api_bp)

    # SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=logging.getLogger('socketio'),
        engineio_logger=False
    )

    # Статика
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('../frontend/dist', path)

    @app.route('/')
    def index():
        return serve_static('index.html')

    return app