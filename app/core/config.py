# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    DEBUG = True
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'database.db'
    )

    UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Desktop', 'ReceivedFiles')
    YT_DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'youtube_downloads')
    MAX_CONTENT_LENGTH = None

    @staticmethod
    def init_app(app):
        for folder in [app.config['UPLOAD_FOLDER'], app.config['YT_DOWNLOAD_FOLDER']]:
            os.makedirs(folder, exist_ok=True)