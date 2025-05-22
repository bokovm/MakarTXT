import os
import logging
import asyncio
import socket
import requests
import threading
from pathlib import Path
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from app import create_app
from app.services.file_service import FileService
from dotenv import load_dotenv

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================
load_dotenv(Path(__file__).parent.parent / '.env')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080/api')

# Глобальные переменные
application = None
bot_thread = None
event_loop = None

# Инициализация Flask app context
flask_app = create_app()

# Настройка логгера
logger = logging.getLogger(__name__)

# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================
def get_frontend_url():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return f"http://{ip}:{os.getenv('FRONTEND_PORT', '3000')}"
    except Exception as e:
        logger.error(f"Ошибка получения IP: {str(e)}")
        return "http://localhost:3000"

def ensure_flask_context(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        with flask_app.app_context():
            return await func(update, context)
    return wrapper

# ======================
# КОМАНДЫ БОТА
# ======================
@ensure_flask_context
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    frontend_url = get_frontend_url()
    message = (
        "🌐 *Веб-интерфейс:*\n"
        f"[{frontend_url}]({frontend_url})\n\n"
        "📋 *Команды:*\n"
        "• `/save текст` - Сохранить текст\n"
        "• `/history` - История файлов\n"
        "• Отправьте файл для сохранения"
    )
    await update.message.reply_text(message, parse_mode='Markdown')

@ensure_flask_context
async def save_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /save"""
    try:
        text = ' '.join(context.args)
        if not text:
            return await update.message.reply_text("❌ Укажите текст для сохранения")
        
        response = requests.post(
            f"{API_BASE_URL}/save_text",
            json={"text": text},
            timeout=10
        )
        
        if response.status_code == 200:
            await update.message.reply_text("✅ Текст сохранен и скопирован в буфер")
        else:
            await update.message.reply_text(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        logger.error(f"Ошибка сохранения текста: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка сервера")

@ensure_flask_context
async def get_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение истории файлов"""
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

@ensure_flask_context
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик загрузки файлов"""
    try:
        file = await update.message.effective_attachment.get_file()
        filename = FileService.sanitize_filename(
            update.message.effective_attachment.file_name
        )
        
        file_bytes = await file.download_as_bytearray()
        
        response = requests.post(
            f"{API_BASE_URL}/files/upload",
            files={'file': (filename, file_bytes)},
            timeout=20
        )
        
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Файл сохранен: {filename}")
        else:
            await update.message.reply_text(f"❌ Ошибка: {response.text}")

    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка загрузки файла")

# ======================
# ОБРАБОТЧИКИ КНОПОК
# ======================
@ensure_flask_context
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    try:
        action, filename = query.data.split(':')
        filename = FileService.sanitize_filename(filename)
        upload_folder = flask_app.config['UPLOAD_FOLDER']
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
            FileService.copy_to_clipboard(content)
            await query.message.reply_text("✅ Текст скопирован в буфер")

    except Exception as e:
        logger.error(f"Ошибка обработки кнопки: {str(e)}")
        await query.message.reply_text("⚠️ Ошибка обработки запроса")

# ======================
# УПРАВЛЕНИЕ БОТОМ
# ======================
def run_bot():
    """Основная функция запуска бота"""
    global application, event_loop
    
    try:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Регистрация обработчиков
        handlers = [
            CommandHandler("start", start),
            CommandHandler("save", save_text_command),
            CommandHandler("history", get_history),
            MessageHandler(filters.Document.ALL, handle_file),
            CallbackQueryHandler(button_handler)
        ]
        
        application.add_handlers(handlers)
        
        logger.info("Бот запущен")
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Ошибка бота: {str(e)}")
        raise

def start_bot():
    """Запуск бота в отдельном потоке"""
    global bot_thread
    
    try:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )
            
        bot_thread = threading.Thread(
            target=run_bot,
            daemon=True,
            name="TelegramBot"
        )
        bot_thread.start()
        logger.info("Бот запущен в отдельном потоке")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {str(e)}")
        raise

def stop_bot():
    """Остановка бота"""
    global application, bot_thread
    
    try:
        if application:
            application.stop()
            logger.info("Бот остановлен")
        if bot_thread and bot_thread.is_alive():
            bot_thread.join(timeout=5)
    except Exception as e:
        logger.error(f"Ошибка остановки бота: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_bot()