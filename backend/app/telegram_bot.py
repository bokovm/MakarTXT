import socket
import os
import asyncio
import logging
import requests
import re
from threading import Thread
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from dotenv import load_dotenv
from app import create_app
from functools import wraps
from flask import has_app_context, current_app
from app.services.file_service import FileService  # Импорт сервиса

# ======================
# НАСТРОЙКИ
# ======================
load_dotenv(Path(__file__).parent.parent / '.env')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080/api')

# Инициализация Flask
flask_app = create_app()

# Настройка логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"IP detection error: {str(e)}")
        return "localhost"
    
def get_frontend_url():
    ip = get_local_ip()
    port = os.getenv("FRONTEND_PORT", "3000")  # Порт из .env или 3000 по умолчанию
    return f"http://{ip}:{port}"

def ensure_flask_context(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not has_app_context():
            with flask_app.app_context():
                return await func(update, context)
        return await func(update, context)
    return wrapper

def get_upload_folder():
    return current_app.config['UPLOAD_FOLDER']

# ======================
# КОМАНДЫ БОТА
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frontend_url = get_frontend_url()
    
    message = (
        "🌐 *Доступ к веб-интерфейсу:*\n"
        f"[{frontend_url}]({frontend_url})\n\n"
        "📋 *Доступные команды:*\n"
        "• `/save текст` - Сохранить текст\n"
        "• `/history` - История файлов\n"
        "• Отправьте файл для сохранения\n"
        "• Используйте кнопки для управления"
    )

    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

@ensure_flask_context
async def save_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = ' '.join(context.args).strip()
        if not text:
            await update.message.reply_text("❌ Введите текст после команды /save")
            return

        response = requests.post(
            f"{API_BASE_URL}/save_text",
            json={"text": text},
            timeout=5
        )

        if response.status_code == 200:
            await update.message.reply_text("✅ Текст сохранен!")
        else:
            await update.message.reply_text(f"❌ Ошибка: {response.text}")

    except Exception as e:
        logger.error(f"Save error: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка сервера")

@ensure_flask_context
async def get_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{API_BASE_URL}/history", timeout=5)
        if response.status_code != 200:
            return await update.message.reply_text("❌ Ошибка загрузки истории")

        history = response.json()
        if not history:
            return await update.message.reply_text("📂 История пуста")

        for item in history:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📥 Скачать", callback_data=f"download:{item['filename']}"),
                    InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{item['filename']}")
                ],
                [InlineKeyboardButton("📋 Копировать", callback_data=f"copy:{item['filename']}")]
            ])
            
            await update.message.reply_text(
                f"📄 *{item['filename']}*\n`{item['content']}`",
                parse_mode='Markdown',
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"History error: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка сервера")

# ======================
# ОБРАБОТЧИКИ ФАЙЛОВ И КНОПОК
# ======================
@ensure_flask_context
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Определяем тип контента
        if update.message.sticker:
            file = await update.message.sticker.get_file()
            ext = '.webp'  # Большинство стикеров в WEBP
            if update.message.sticker.is_animated:
                ext = '.tgs'  # Анимированные стикеры
            elif update.message.sticker.is_video:
                ext = '.webm'  # Видеостикеры
            filename = f"sticker_{update.message.message_id}{ext}"
        else:
            file = await update.message.effective_attachment.get_file()
            filename = FileService.sanitize_filename(update.message.effective_attachment.file_name)
        
        # Скачивание файла
        file_bytes = await file.download_as_bytearray()
        
        # Сохранение через API
        response = requests.post(
            f"{API_BASE_URL}/files/upload",
            files={'file': (filename, file_bytes)},
            timeout=20
        )
        
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Стикер сохранен!\nИмя: {filename}" 
                                          if update.message.sticker 
                                          else f"✅ Файл сохранен!\nИмя: {filename}")
        else:
            await update.message.reply_text(f"❌ Ошибка: {response.text}")

    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка загрузки файла")

@ensure_flask_context
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        action, filename = query.data.split(':')
        filename = FileService.sanitize_filename(filename)
        upload_folder = get_upload_folder()
        filepath = Path(upload_folder) / filename

        if action == 'download':
            if not filepath.exists():
                return await query.message.reply_text("❌ Файл не найден")
            
            await query.message.reply_document(
                document=open(filepath, 'rb'),
                caption=f"📥 {filename}"
            )

        elif action == 'delete':
            response = requests.delete(f"{API_BASE_URL}/files/delete/{filename}")
            if response.status_code == 200:
                await query.message.edit_text(f"🗑 Файл удален: {filename}")
            else:
                await query.message.reply_text(f"❌ Ошибка: {response.text}")

        elif action == 'copy':
            response = requests.get(f"{API_BASE_URL}/files/content/{filename}")
            if response.status_code != 200:
                return await query.message.reply_text("❌ Ошибка копирования")
            
            content = response.json().get('content', '')
            # Кроссплатформенное копирование
            if os.name == 'posix':
                os.system(f'echo "{content}" | xclip -selection clipboard')
            else:
                os.system(f'echo {content} | clip')
            
            await query.message.reply_text("✅ Текст скопирован в буфер")

    except Exception as e:
        logger.error(f"Button error: {str(e)}")
        await query.message.reply_text("⚠️ Ошибка обработки запроса")

# ======================
# ЗАПУСК БОТА
# ======================
def run_bot():
    with flask_app.app_context():
        test_files = FileService.get_history_files()
        logger.info(f"Test history files: {test_files}")
        logger.info(f"Upload folder: {current_app.config['UPLOAD_FOLDER']}")
    """Основная функция запуска бота с обработкой event loop"""
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Регистрация обработчиков
        handlers = [
            CommandHandler("start", start),
            CommandHandler("help", start),
            CommandHandler("save", save_text),
            CommandHandler("history", get_history),
            MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.Sticker.ALL, handle_file),
            CallbackQueryHandler(button_handler)
        ]
        
        application.add_handlers(handlers)
        
        logger.info("Запуск бота с новым event loop")
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False  # Важно для работы в отдельном потоке
        )
    except Exception as e:
        logger.error(f"Ошибка в run_bot: {str(e)}")
        raise

def start_bot():
    """Запуск бота в отдельном потоке"""
    try:
        # Настройка asyncio для Windows
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        bot_thread = Thread(
            target=run_bot,
            daemon=True,
            name="TelegramBotThread"
        )
        bot_thread.start()
        logger.info("Telegram бот запущен в отдельном потоке")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {str(e)}")
        raise

if __name__ == "__main__":
    # Для прямого запуска бота (без Flask)
    run_bot()