from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit
import yt_dlp
from app.services.youtube_service import YouTubeService
from app.core.exceptions import YouTubeDownloadError
from app import socketio
import re

youtube_bp = Blueprint('youtube', __name__)

@youtube_bp.route('/info')
def get_video_info():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify(error="URL обязателен"), 400

    if not YouTubeService.validate_url(url):
        return jsonify(error="Некорректный YouTube URL"), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = [{
                'format_id': f['format_id'],
                'resolution': f.get('resolution', 'unknown'),
                'ext': f['ext'],
                'filesize': f.get('filesize_approx')
            } for f in info['formats'] if f.get('video_ext') == 'mp4']

        return jsonify({
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'formats': formats
        })
        
    except Exception as e:
        current_app.logger.error(f"Ошибка получения информации: {str(e)}")
        return jsonify(error="Не удалось получить информацию о видео"), 500

@youtube_bp.route('/search')
def youtube_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify(error="Query parameter 'q' is required"), 400

    try:
        results = YouTubeService.search_videos(query)
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify(error="Search failed"), 500

@youtube_bp.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url or not YouTubeService.validate_url(url):
            return jsonify(error="Некорректный URL"), 400

        filename, title = YouTubeService.download_video(
            url, 
            Path(current_app.config['YT_DOWNLOAD_FOLDER'])
        )

        return jsonify(
            success=True,
            filename=filename,
            title=title,
            download_url=f"/youtube/downloads/{filename}"
        )

    except YouTubeDownloadError as e:
        current_app.logger.error(f"Ошибка загрузки: {str(e)}")
        return jsonify(error=str(e)), 500
    except Exception as e:
        current_app.logger.critical(f"Критическая ошибка: {str(e)}")
        return jsonify(error="Внутренняя ошибка сервера"), 500