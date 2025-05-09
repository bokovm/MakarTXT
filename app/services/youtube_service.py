import re
import yt_dlp
from datetime import datetime
import os
from ..core.exceptions import YouTubeDownloadError

class YouTubeService:
    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        patterns = [
            r'^https?://(www\.)?youtube\.com/watch\?v=',
            r'^https?://youtu\.be/'
        ]
        return any(re.search(p, url) for p in patterns)

    @classmethod
    def download_video(cls, url: str, download_dir: str) -> tuple[str, str]:
        download_dir = os.path.abspath(download_dir)
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'progress_hooks': [cls._progress_hook]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return os.path.basename(filename), info.get('title', 'video')
        except Exception as e:
            raise YouTubeDownloadError(f"Ошибка загрузки: {str(e)}")

    @staticmethod
    def _progress_hook(d):
        if d['status'] == 'downloading':
            print(f"Прогресс: {d['_percent_str']} Скорость: {d['_speed_str']}")