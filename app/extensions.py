# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS
cors = CORS(supports_credentials=True)
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

db = SQLAlchemy()
socketio = SocketIO()