import os
import re
import logging
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from threading import Thread
from typing import List, Dict, Union
from flask import current_app

logger = logging.getLogger(__name__)


class FileService:
    _app = None

    @classmethod
    def init_app(cls, app):
        cls._app = app
        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)  # Создаем папку при запуске
        logger.info(f"Upload folder: {upload_folder}")

    @classmethod
    def get_upload_folder(cls):
        with cls._app.app_context():
            return current_app.config['UPLOAD_FOLDER']
        
    @classmethod
    def get_history_files(cls) -> List[dict]:
        upload_folder = cls.get_upload_folder()
        logger.info(f"Checking history in: {upload_folder}")
        
        try:
            files = list(Path(upload_folder).glob('*.txt'))
            logger.info(f"Found {len(files)} text files")
            
            history = []
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(500)
                    history.append({
                        "filename": file_path.name,
                        "content": content,
                        "created": os.path.getctime(file_path)
                    })
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
            
            return sorted(history, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logger.error(f"History error: {str(e)}", exc_info=True)
            return []

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "", filename).strip()[:255]

    @classmethod
    def handle_file_upload(cls, file) -> Dict[str, Union[bool, str]]:
        if not file or file.filename == '':
            raise ValueError("Invalid filename")

        try:
            filename = cls.sanitize_filename(file.filename)
            upload_folder = cls.get_upload_folder()
            filepath = os.path.join(upload_folder, filename)
            
            file.save(filepath)
            logger.info(f"File saved: {filepath}")

            if filename.lower().endswith('.txt'):
                cls._open_file_in_thread(filepath)
                cls._copy_to_clipboard(Path(filepath).read_text(encoding='utf-8'))

            return {'success': True, 'filename': filename}
        except Exception as e:
            logger.error(f"Upload error: {str(e)}", exc_info=True)
            raise

    @classmethod
    def save_text(cls, text: str):
        try:
            # Получаем папку из конфига
            upload_folder = cls._app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            # Генерируем имя файла
            filename = f"text_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            filepath = os.path.join(upload_folder, filename)

            # Сохраняем файл
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

            # Копируем в буфер
            cls._copy_to_clipboard(text)

            # Открываем файл
            cls._open_file_in_thread(filepath)

            return {"status": "success", "path": filepath}
        except Exception as e:
            logger.error(f"Ошибка сохранения: {str(e)}")
            return {"status": "error", "message": str(e)}

    @classmethod
    def _copy_to_clipboard(cls, text):
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except:
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                win32clipboard.CloseClipboard()
                return True
            except Exception as e:
                logger.error(f"Clipboard error: {str(e)}")
                return False

    @classmethod
    def _open_file_in_thread(cls, filepath: str):
        def opener():
            try:
                if platform.system() == 'Windows':
                    os.startfile(filepath)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', filepath])
                else:
                    subprocess.run(['xdg-open', filepath])
            except Exception as e:
                logger.error(f"Open file error: {str(e)}")

        Thread(target=opener, daemon=True).start()

    @classmethod
    def list_files(cls) -> List[Dict]:
        upload_folder = cls.get_upload_folder()
        files = []
        
        try:
            for f in sorted(os.listdir(upload_folder), key=lambda x: os.path.getctime(os.path.join(upload_folder, x))):
                full_path = os.path.join(upload_folder, f)
                if os.path.isfile(full_path):
                    files.append({
                        "name": f,
                        "path": full_path,
                        "size": os.path.getsize(full_path),
                        "created": datetime.fromtimestamp(os.path.getctime(full_path))
                    })
        except Exception as e:
            logger.error(f"List files error: {str(e)}")
        
        return files