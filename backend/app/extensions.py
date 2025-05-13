from flask_socketio import SocketIO
from .socket_handlers import ChatNamespace, ProgressNamespace

socketio = SocketIO(cors_allowed_origins="*")

def init_socketio(app):
    socketio.init_app(
        app,
        async_mode='eventlet',
        logger=True,
        engineio_logger=False
    )
    socketio.on_namespace(ChatNamespace('/chat'))
    socketio.on_namespace(ProgressNamespace('/progress'))