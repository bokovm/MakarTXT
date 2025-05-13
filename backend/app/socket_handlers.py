from flask import request
from flask_socketio import Namespace, emit
from app.services.auth_service import validate_token
from celery.result import AsyncResult

class ProgressNamespace(Namespace):
    def on_connect(self):
        try:
            # Проверка аутентификации
            token = request.args.get('token')
            validate_token(token)
            print('Progress client connected')
        except Exception as e:
            print(f'Connection error: {str(e)}')
            self.disconnect()

    def on_disconnect(self):
        print('Progress client disconnected')

    def on_get_progress(self, data):
        task_id = data.get('task_id')
        if not task_id:
            return emit('error', {'message': 'Task ID required'})
        
        try:
            task = AsyncResult(task_id)
            if task.state == 'PROGRESS':
                emit('progress_update', {
                    'progress': task.info.get('progress', 0),
                    'speed': task.info.get('speed', 'N/A')
                })
            elif task.state == 'SUCCESS':
                emit('download_complete', {
                    'filename': task.result,
                    'path': f"/downloads/{task.result}"
                })
            elif task.state == 'FAILURE':
                emit('error', {'message': str(task.info)})
        except Exception as e:
            emit('error', {'message': f"Progress check failed: {str(e)}"})

class ChatNamespace(Namespace):
    def on_connect(self):
        try:
            token = request.args.get('token')
            validate_token(token)
            print('Chat client connected')
        except Exception as e:
            print(f'Connection error: {str(e)}')
            self.disconnect()

    def on_disconnect(self):
        print('Chat client disconnected')

    def on_message(self, data):
        try:
            # Логика обработки сообщений чата
            self.emit('message_response', {
                'status': 'received',
                'content': data.get('content')
            })
        except Exception as e:
            emit('error', {'message': str(e)})