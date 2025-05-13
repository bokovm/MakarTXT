# app/blueprints/chat/routes.py
from datetime import datetime
import os
from pathlib import Path
from flask import Blueprint, Response, app, current_app, request, jsonify, send_from_directory
from flask_socketio import emit
from app.services.file_service import FileService
from app.services.config_service import get_config, save_config
from app import socketio

chat_bp = Blueprint('chat', __name__, template_folder='templates')

@chat_bp.route('/')
def index():
    """Главная страница чата"""
    files = FileService.list_files()
    messages = FileService.prepare_messages(files)
    return app.send_static_file('index.html')

@chat_bp.route('/api/history')
def get_history():
    try:
        files = FileService.get_history_files()
        return jsonify([{
            'filename': f.name,
            'content': f.read_text(encoding='utf-8', errors='replace'),
            'timestamp': f.stat().st_mtime
        } for f in files if f.is_file()])
    except Exception as e:
        return jsonify(error=str(e)), 500

@chat_bp.route('/api/messages')
def get_messages():
    try:
        files = FileService.list_files()
        messages = FileService.prepare_messages(files)
        
        # Добавляем проверку на ошибки чтения файлов
        for msg in messages:
            if 'error' in msg:
                current_app.logger.warning(f"Поврежденный файл: {msg.get('filename')}")
                
        return jsonify(messages)
    except Exception as e:
        current_app.logger.error(f"Ошибка в /api/messages: {str(e)}")
        return jsonify({"error": "Ошибка загрузки сообщений", "details": str(e)}), 500

@chat_bp.route('/get_files')
def get_files():
    files = FileService.list_files()
    return jsonify([{
        'name': Path(f).name,
        'size': Path(f).stat().st_size
    } for f in files])

@chat_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(error="Файл не выбран"), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="Неверное имя файла"), 400

    try:
        filename = FileService.sanitize_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        return jsonify(success=True, filename=filename)
    except Exception as e:
        return jsonify(error=str(e)), 500

@chat_bp.route('/api/save_text', methods=['POST'])
def save_text():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify(error="Текст сообщения не может быть пустым"), 400
    
    try:
        message = FileService.save_text(text)
        socketio.emit('message_update', message, broadcast=True)  # Добавлено
        return jsonify(message)
    except Exception as e:
        return jsonify(error=str(e)), 500
    
@socketio.on('new_message')
def handle_new_message(data):
    """Обработка нового сообщения через WebSocket"""
    try:
        text = data.get('text', '').strip()
        if not text:
            return
        
        # Сохраняем только как txt
        message = FileService.save_text(text)
        
        # Копируем только для txt
        if get_config().get("copy_to_clipboard", True):
            FileService.copy_to_clipboard(text)
            
        emit('message_update', {
            'type': 'text',
            'content': text,
            'time': datetime.now().strftime('%H:%M'),
            'filename': message['filename'],
            'autoCopy': True
        }, broadcast=True)
    except Exception as e:
        current_app.logger.error(f"Ошибка обработки сообщения: {str(e)}")

@chat_bp.route('/file/<filename>')
def download_file(filename):
    """Скачивание файла"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)):
        return jsonify(error="Файл не найден"), 404
    
    if filename.endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if request.headers.get('Accept', '').lower() == 'text/plain':
                return content
            
            if get_config().get("copy_to_clipboard", True):
                FileService.copy_to_clipboard(content)
            
            return Response(content, mimetype='text/plain')
        except Exception as e:
            current_app.logger.error(f"Ошибка обработки файла: {str(e)}")
            return jsonify(error="Ошибка обработки файла"), 500
    
    return send_from_directory(upload_folder, filename, as_attachment=True)

# WebSocket обработчики
@socketio.on('connect')
def handle_connect():
    current_app.logger.info("Клиент подключен")

@socketio.on('disconnect')
def handle_disconnect():
    current_app.logger.info("Клиент отключен")

@socketio.on('refresh_messages')
def handle_refresh():
    """Обновление списка сообщений"""
    try:
        files = FileService.list_files()
        messages = FileService.prepare_messages(files)
        emit('messages_refreshed', messages, broadcast=True)
    except Exception as e:
        current_app.logger.error(f"Ошибка обновления сообщений: {str(e)}")

# API для работы с буфером обмена
@chat_bp.route("/clipboard/state", methods=['GET', 'POST'])
def clipboard_state():
    """Управление настройками буфера обмена"""
    if request.method == 'GET':
        return jsonify(enabled=get_config().get("copy_to_clipboard", True))
    
    if request.method == 'POST':
        try:
            state = request.json.get("enabled", True)
            config = get_config()
            config["copy_to_clipboard"] = bool(state)
            save_config(config)
            return jsonify(success=True)
        except Exception as e:
            current_app.logger.error(f"Ошибка изменения настроек: {str(e)}")
            return jsonify(error="Ошибка сервера"), 500