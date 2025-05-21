import re
import time
import requests
import yt_dlp
from pathlib import Path
from typing import Tuple
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential
from ..core.exceptions import YouTubeDownloadError
from socket import gaierror
from urllib3.exceptions import NewConnectionError

class YouTubeService:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Проверка валидности YouTube URL"""
        patterns = [
            r'^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)',
            r'^https?://(www\.)?music\.youtube\.com/watch\?v='
        ]
        return any(re.match(p, url) for p in patterns)

    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def download_video(cls, url: str, download_dir: Path) -> Tuple[str, str]:
        """
        Основной метод загрузки с автоматическим переключением
        между yt-dlp и RapidAPI при ошибках
        """
        try:
            return cls._download_ytdlp(url, download_dir)
        except Exception as e:
            current_app.logger.warning(f"yt-dlp failed: {str(e)}, trying RapidAPI")
            return cls._download_via_rapidapi(url, download_dir)

    @classmethod
    def _download_ytdlp(cls, url: str, download_dir: Path) -> Tuple[str, str]:
        """Загрузка через yt-dlp с настройками из конфига"""
        ydl_opts = {
            **current_app.config['YDL_OPTS'],
            'outtmpl': str(download_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [cls._progress_hook],
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return Path(filename).name, info.get('title', 'video')
        except (gaierror, NewConnectionError) as e:
            raise YouTubeDownloadError("Ошибка подключения. Проверьте интернет и настройки прокси")
        except Exception as e:
            raise YouTubeDownloadError(f"yt-dlp error: {str(e)}")

    @classmethod
    def _download_via_rapidapi(cls, url: str, download_dir: Path) -> Tuple[str, str]:
        """Резервный метод через RapidAPI"""
        api_url = "https://youtube138.p.rapidapi.com/download/"
        params = {
            "url": url,
            "format": "mp4",
            "quality": "720p"
        }
        headers = {
            "X-RapidAPI-Key": current_app.config['RAPIDAPI_KEY'],
            "X-RapidAPI-Host": "youtube138.p.rapidapi.com"
        }

        try:
            # Получаем информацию о видео для имени файла
            info = cls._get_basic_info(url)
            title = info.get('title', f'video_{int(time.time())}')
            safe_title = re.sub(r'[^\w\-_]', '_', title)[:100]
            filename = f"{safe_title}.mp4"
            filepath = download_dir / filename

            # Загрузка контента
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(response.content)

            return filename, title
        except Exception as e:
            raise YouTubeDownloadError(f"RapidAPI error: {str(e)}")

    @classmethod
    def _get_basic_info(cls, url: str) -> dict:
        """Получение базовой информации о видео"""
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'proxy': current_app.config['YDL_OPTS'].get('proxy')
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    def _progress_hook(d: dict):
        """Хук для отслеживания прогресса загрузки"""
        if d['status'] == 'downloading':
            progress = {
                'percent': d.get('_percent_str', '0%'),
                'speed': d.get('_speed_str', 'N/A'),
                'eta': d.get('_eta_str', 'N/A')
            }
            current_app.logger.info(f"Прогресс загрузки: {progress}")

    @classmethod
    def search_videos(cls, query: str) -> dict:
        """Поиск видео через RapidAPI"""
        url = "https://youtube138.p.rapidapi.com/search/"
        params = {
            "q": query,
            "hl": "en",
            "gl": "US",
            "type": "video"
        }
        headers = {
            "X-RapidAPI-Key": current_app.config['RAPIDAPI_KEY'],
            "X-RapidAPI-Host": current_app.config['RAPIDAPI_HOST']
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return self._parse_search_results(response.json())
        except requests.exceptions.RequestException as e:
            raise YouTubeDownloadError(f"Ошибка поиска: {str(e)}")

    @classmethod
    def _parse_search_results(cls, data: dict) -> dict:
        """Парсинг результатов поиска"""
        return {
            'items': [{
                'videoId': item['videoId'],
                'title': item['title'],
                'thumbnail': item['thumbnails'][0]['url'] if item['thumbnails'] else '',
                'duration': item['lengthSeconds'],
                'viewCount': item['viewCount']
            } for item in data.get('contents', []) if item.get('videoId')]
        }