# app/services/file_service.py
from pathlib import Path
import pyperclip
import os
import re
import logging
import platform
import subprocess
from datetime import datetime, time
from threading import Thread
from typing import Dict, List, Optional, Union
from flask import current_app
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from app.services.config_service import get_config

class FileService:
    @staticmethod
    def get_history_files():
        upload_folder = current_app.config['UPLOAD_FOLDER']
        try:
            return list(Path(upload_folder).glob('*.txt'))
        except Exception as e:
            current_app.logger.error(f"FileService error: {str(e)}")
            return []

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Очищает имя файла от запрещенных символов"""
        return re.sub(r'[\\/*?:"<>|]', "", filename).strip()[:255]

    @classmethod
    def handle_file_upload(cls, file) -> Dict[str, Union[bool, str]]:
        """Обрабатывает загрузку файла"""
        if not file or file.filename == '':
            raise ValueError("Неверное имя файла")

        try:
            filename = cls.sanitize_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Создаем папку если не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            file.save(filepath)
            cls.open_file_in_thread(filepath)
            
            return {'success': True, 'filename': filename}
        except Exception as e:
            current_app.logger.error(f"Ошибка загрузки файла: {str(e)}")
            raise

    @classmethod
    def save_text(cls, text: str):
        try:
            # Создаем папку, если ее нет
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            # Сохраняем файл
            filename = f"text_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            filepath = os.path.join(upload_folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

            # Копируем в буфер
            cls.copy_to_clipboard(text)
            
            # Открываем файл
            os.startfile(filepath)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def copy_to_clipboard(text):
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception as e:
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                win32clipboard.CloseClipboard()
                return True
            except Exception as e:
                current_app.logger.error(f"Ошибка копирования: {str(e)}")
                return False

    @staticmethod
    def open_file_in_thread(filepath: str) -> None:
        def _open_file():
            try:
                import win32gui
                import win32con
                import win32process
                import time

                process = subprocess.Popen(
                    ["notepad.exe", filepath],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                time.sleep(0.5)
                pid = process.pid

                def callback(hwnd, hwnds):
                    if win32gui.IsWindowVisible(hwnd):
                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if found_pid == pid:
                            hwnds.append(hwnd)
                    return True

                hwnds = []
                win32gui.EnumWindows(callback, hwnds)
                
                if hwnds:
                    hwnd = hwnds[0]
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                    )
                    win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                os.startfile(filepath)
                current_app.logger.error(f"Ошибка открытия файла: {str(e)}")

        Thread(target=_open_file).start()

    @staticmethod
    def list_files() -> List[str]:
        """Возвращает список файлов в папке загрузок"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            return []
            
        return [
            os.path.join(upload_folder, f) 
            for f in os.listdir(upload_folder)
            if os.path.isfile(os.path.join(upload_folder, f))
        ]

    @staticmethod
    def prepare_messages(files: List[str]) -> List[Dict]:
        """Подготавливает сообщения для отображения"""
        messages = []
        encodings = ['utf-8', 'windows-1251', 'cp866', 'iso-8859-1']
        
        for filepath in sorted(files, key=os.path.getctime):
            filename = os.path.basename(filepath)
            created = datetime.fromtimestamp(os.path.getctime(filepath))
            message = {
                'filename': filename,
                'time': created.strftime('%H:%M'),
                'type': 'text' if filename.endswith('.txt') else 'file'
            }

            if message['type'] == 'text':
                content = None
                for encoding in encodings:
                    try:
                        with open(filepath, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        current_app.logger.error(f"Ошибка чтения файла {filename}: {str(e)}")
                
                message['content'] = content or "⚠️ Не удалось отобразить содержимое файла"
            else:
                try:
                    message['size'] = os.path.getsize(filepath)
                except Exception as e:
                    current_app.logger.error(f"Ошибка получения размера файла: {str(e)}")
                    message['size'] = 0

            messages.append(message)
        
        return messages