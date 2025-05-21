from pathlib import Path
from flask import Blueprint, jsonify, request, current_app, send_from_directory
from flask_socketio import emit
import socketio
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from ..services.file_service import FileService
from ..services.youtube_service import YouTubeService
from ..core.exceptions import InvalidFileError, YouTubeDownloadError
from ..services.log_service import log_access

bp = Blueprint('api', __name__, url_prefix='/api')

# Сообщения
@bp.route('/save_text', methods=['POST'])
def save_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        result = FileService.save_text(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/messages', methods=['GET'])
def get_messages():
    try:
        files = FileService.list_files()
        messages = FileService.prepare_messages(files)
        return jsonify(messages)
    except Exception as e:
        current_app.logger.error(f"Messages error: {str(e)}")
        return jsonify({"error": "Ошибка загрузки сообщений"}), 500

# История файлов
@bp.route('/history', methods=['GET'])
def get_history():
    try:
        files = FileService.get_history_files()
        return jsonify(files)
    except Exception as e:
        current_app.logger.error(f"History error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Загрузка файлов
@bp.route('/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        result = FileService.handle_file_upload(file)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Управление файлами
@bp.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        safe_filename = secure_filename(filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "Файл не найден"}), 404
            
        os.remove(file_path)
        emit('file_deleted', {'filename': safe_filename}, namespace='/', broadcast=True)
        return jsonify({"status": "Файл удален"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route('/files/download/<filename>', methods=['GET'])
def download_file_route(filename):
    try:
        safe_filename = FileService.sanitize_filename(filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(
            upload_folder,
            safe_filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 404
    
@bp.route('/files/delete/<filename>', methods=['DELETE'])
def delete_file_handler(filename):  # Изменили имя функции
    try:
        from app.services.file_service import FileService
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = Path(upload_folder) / filename
        
        if not filepath.exists():
            return jsonify({"error": "File not found"}), 404
            
        filepath.unlink()
        return jsonify({"status": "success"})
        
    except Exception as e:
        current_app.logger.error(f"Delete error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# YouTube интеграция
@bp.route('/youtube/download', methods=['POST'])
def download_youtube():
    data = request.json
    url = data.get('url')
    format_id = data.get('format', 'best')
    
    if not url:
        return jsonify({"error": "URL обязателен"}), 400

    try:
        if not YouTubeService.validate_url(url):
            return jsonify({"error": "Неверный YouTube URL"}), 400

        filename, title = YouTubeService.download_video(
            url,
            current_app.config['YT_DOWNLOAD_FOLDER']
        )
        
        emit('youtube_progress', {
            'status': 'complete',
            'filename': filename,
            'title': title
        }, namespace='/', broadcast=True)
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "download_url": f"/downloads/{filename}"
        })
    except YouTubeDownloadError as e:
        return jsonify({"error": str(e)}), 500

# Веб-сокет события
@bp.route('/socket')
def handle_socket_connection():
    @socketio.on('connect')
    def on_connect():
        emit('connection_status', {'status': 'connected'})

    @socketio.on('new_message')
    def handle_new_message(data):
        emit('new_message', data, broadcast=True)

    @socketio.on('request_progress')
    def handle_progress_request(data):
        # Логика обновления прогресса
        emit('download_progress', {'progress': 0})

# Вспомогательные эндпоинты
@bp.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        "max_file_size": current_app.config['MAX_CONTENT_LENGTH'],
        "allowed_extensions": current_app.config['ALLOWED_EXTENSIONS']
    })

@bp.route('/downloads/<filename>')
def download_file(filename):
    safe_filename = secure_filename(filename)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        safe_filename,
        as_attachment=True
    )