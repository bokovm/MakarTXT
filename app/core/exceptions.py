# app/core/exceptions.py
class InvalidFileError(Exception):
    """Некорректный файл"""
    pass

class YouTubeDownloadError(Exception):
    """Ошибка загрузки YouTube видео"""
    pass

class FileProcessingError(Exception):
    """Ошибка обработки файла"""
    pass
