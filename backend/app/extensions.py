# backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()

def init_extensions(app):
    db.init_app(app)
    socketio.init_app(app,
        cors_allowed_origins="*",
        async_mode='eventlet'
    )