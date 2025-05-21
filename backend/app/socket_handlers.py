# backend/app/socket_handlers.py
from flask_socketio import Namespace
from app.services.auth_service import validate_token  # Создайте этот сервис

from flask_socketio import Namespace

class ChatNamespace(Namespace):
    def on_connect(self):
        try:
            print('Client connected')
        except Exception as e:
            print(f'Connection error: {str(e)}')
            self.disconnect()

    def on_disconnect(self):
        print('Client disconnected')

    def on_message(self, data):
        try:
            # Обработка сообщения
            self.emit('response', {'status': 'received'})
        except Exception as e:
            self.emit('error', {'message': str(e)})

# Инициализация в extensions.py
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

def init_socketio(app):
    socketio.init_app(app)
    socketio.on_namespace(ChatNamespace('/chat'))