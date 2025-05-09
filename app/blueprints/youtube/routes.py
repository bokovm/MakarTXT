# app/blueprints/youtube/routes.py
from flask import Blueprint, jsonify, request, current_app
from flask_socketio import emit
import yt_dlp
import os
import re
import uuid
from threading import Thread, Lock
from app import socketio

youtube_bp = Blueprint(
    'youtube',
    __name__,
    template_folder='templates',
    static_folder='static'
)
downloads_lock = Lock()
downloads = {}

def async_download(url, download_id):
    try:
        download_dir = current_app.config['YT_DOWNLOAD_FOLDER']
        os.makedirs(download_dir, exist_ok=True)
        
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
            'quiet': True,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        }

        with downloads_lock:
            downloads[download_id] = {
                'status': 'downloading',
                'progress': '0%',
                'filename': None
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            with downloads_lock:
                downloads[download_id] = {
                    'status': 'completed',
                    'progress': '100%',
                    'filename': os.path.basename(filename),
                    'title': info.get('title', 'video'),
                    'url': f"/youtube/download/{os.path.basename(filename)}"
                }

    except Exception as e:
        with downloads_lock:
            downloads[download_id] = {
                'status': 'error',
                'message': str(e)
            }

def progress_hook(d, download_id):
    if d['status'] == 'downloading':
        with downloads_lock:
            if download_id in downloads:
                downloads[download_id]['progress'] = d.get('_percent_str', '0%')
                socketio.emit('download_progress', {
                    'id': download_id,
                    'progress': downloads[download_id]['progress']
                })

@youtube_bp.route('/download/start', methods=['POST'])
def start_download():
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not re.match(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}', url):
        return jsonify(error="Invalid YouTube URL"), 400

    download_id = str(uuid.uuid4())
    
    Thread(target=async_download, args=(url, download_id)).start()
    
    return jsonify({
        'status': 'started',
        'download_id': download_id
    })

@youtube_bp.route('/download/status/<download_id>')
def check_status(download_id):
    with downloads_lock:
        return jsonify(downloads.get(download_id, {'status': 'not_found'}))

@youtube_bp.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(
        current_app.config['YT_DOWNLOAD_FOLDER'],
        filename,
        as_attachment=True
    )