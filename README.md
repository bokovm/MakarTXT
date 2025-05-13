# MakarTXT - Локальный менеджер текста и медиа

![Логотип](frontend/public/logo.jpg)

Универсальное приложение для управления текстовыми заметками, файлами и загрузки YouTube видео. 
Работает локально на вашем ПК с поддержкой Telegram-бота.

## 🌟 Особенности
- **Текстовый редактор** с автосохранением и историей
- **Файловый менеджер** с поддержкой загрузки/скачивания
- **YouTube Downloader** с выбором качества
- **Telegram-бот** для удаленного управления
- Веб-сокеты для real-time обновлений
- Темная/светлая темы
- Кроссплатформенная поддержка (Windows/Linux/macOS)

## 🚀 Запуск проекта

### Требования
- Python 3.10+
- Node.js 18+
- Docker (опционально)

### 1. Настройка backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

pip install -r requirements.txt

# Создать .env файл
echo "SECRET_KEY=ваш_секретный_ключ" > .env
echo "RAPIDAPI_KEY=ваш_ключ" >> .env

Настройка frontend
cd frontend
npm install

Запуск
# В одном терминале
cd backend && python run.py

# В другом терминале
cd frontend && npm run dev

Docker-версия
docker-compose up --build

🛠 Использование
Откройте http://localhost:5173

Основные функции:

Текст: Сохраняйте текстовые заметки с авто-копированием в буфер

Файлы: Перетаскивайте файлы в интерфейс

YouTube: Вставьте ссылку → выберите формат → скачайте

Telegram: Настройте бота через /start