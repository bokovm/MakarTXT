from flask import Flask, request, send_from_directory, render_template_string, jsonify, abort
import os
from datetime import datetime
import re
import logging
import time
import pytube
import socket
import platform
from user_agents import parse

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация папок
UPLOAD_FOLDER = 'uploads'
YT_DOWNLOAD_FOLDER = 'youtube_downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(YT_DOWNLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['YT_DOWNLOAD_FOLDER'] = YT_DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = None  # Без ограничений

# Для защиты от выхода во время загрузки
active_downloads = {}

def get_client_info():
    """Получаем информацию об устройстве клиента"""
    user_agent = parse(request.headers.get('User-Agent', ''))
    client_ip = request.remote_addr or 'unknown'
    
    try:
        hostname = socket.gethostbyaddr(client_ip)[0]
    except (socket.herror, socket.gaierror):
        hostname = 'unknown'
    except Exception as e:
        logger.error(f"Ошибка получения hostname: {str(e)}")
        hostname = 'error'

    return {
        'ip': client_ip,
        'platform': user_agent.os.family,
        'browser': user_agent.browser.family,
        'device': user_agent.device.family,
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'hostname': hostname
    }

def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    return filename.strip()

def log_access():
    """Логируем информацию о посещении"""
    client_info = get_client_info()
    logger.info(
        f"Новое подключение: IP={client_info['ip']}, "
        f"Устройство={client_info['device']}, "
        f"ОС={client_info['platform']}, "
        f"Браузер={client_info['browser']}, "
        f"Мобильное={client_info['is_mobile']}, "
        f"URL={request.url}"
    )

@app.route('/')
def index():
    log_access()
    files = os.listdir(app.config['UPLOAD_FOLDER']) if os.path.exists(app.config['UPLOAD_FOLDER']) else []
    
    # Получаем историю сообщений
    messages = []
    for filename in sorted(files, key=lambda x: os.path.getctime(os.path.join(app.config['UPLOAD_FOLDER'], x))):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        created = datetime.fromtimestamp(os.path.getctime(filepath))
        
        if filename.endswith('.txt'):
            content = None
            encodings = ['utf-8', 'windows-1251', 'cp866', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Ошибка чтения файла {filename}: {str(e)}")
                    content = None
                    break

            if content is None:
                logger.warning(f"Не удалось прочитать файл {filename} в поддерживаемых кодировках")
                content = "⚠️ Не удалось отобразить содержимое файла"

            messages.append({
                'type': 'text',
                'content': content,
                'time': created.strftime('%H:%M'),
                'filename': filename
            })
        else:
            messages.append({
                'type': 'file',
                'filename': filename,
                'time': created.strftime('%H:%M'),
                'size': os.path.getsize(filepath)
            })
    
    return render_template_string("""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {
                    --primary-color: #0088cc;
                    --message-bg: #e3f2fd;
                    --my-message-bg: #d1edff;
                    --input-bg: #f5f5f5;
                    --yt-red: #ff0000;
                }
                body {
                    font-family: 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f1f1f1;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                .header {
                    background-color: var(--primary-color);
                    color: white;
                    padding: 15px;
                    font-size: 18px;
                    font-weight: bold;
                    text-align: center;
                }
                .chat-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 10px;
                    background-color: #e6ebee;
                }
                .message {
                    max-width: 80%;
                    margin-bottom: 10px;
                    padding: 8px 12px;
                    border-radius: 7.5px;
                    position: relative;
                    word-wrap: break-word;
                }
                .text-message {
                    background-color: var(--my-message-bg);
                    align-self: flex-end;
                    margin-left: auto;
                }
                .file-message {
                    background-color: var(--message-bg);
                    align-self: flex-start;
                }
                .message-time {
                    font-size: 11px;
                    color: #666;
                    margin-top: 4px;
                    text-align: right;
                }
                .file-info {
                    display: flex;
                    align-items: center;
                }
                .file-icon {
                    margin-right: 10px;
                    color: var(--primary-color);
                }
                .input-area {
                    background-color: white;
                    padding: 10px;
                    display: flex;
                    align-items: center;
                    border-top: 1px solid #ddd;
                }
                .text-input {
                    flex: 1;
                    border: none;
                    border-radius: 20px;
                    padding: 10px 15px;
                    background-color: var(--input-bg);
                    outline: none;
                }
                .attach-btn {
                    margin: 0 10px;
                    color: var(--primary-color);
                    cursor: pointer;
                    background: none;
                    border: none;
                    font-size: 20px;
                }
                .send-btn {
                    background-color: var(--primary-color);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                }
                #file-input {
                    display: none;
                }
                #progress-container {
                    display: none;
                    margin: 10px 0;
                    padding: 8px;
                    background: #f0f0f0;
                    border-radius: 5px;
                }
                #progress-bar {
                    width: 100%;
                    height: 5px;
                    background: #ddd;
                    border-radius: 3px;
                    overflow: hidden;
                }
                #progress {
                    width: 0%;
                    height: 100%;
                    background: var(--primary-color);
                    transition: width 0.1s ease;
                }
                #progress-info {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 5px;
                    font-size: 12px;
                    color: #666;
                }
                .download-section {
                    margin: 15px;
                    padding: 15px;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .download-input {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    margin-bottom: 10px;
                    box-sizing: border-box;
                }
                .download-btn {
                    background-color: var(--yt-red);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    cursor: pointer;
                    width: 100%;
                }
                .download-btn:hover {
                    background-color: #cc0000;
                }
                #before-unload-message {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: #ffcc00;
                    padding: 10px;
                    text-align: center;
                    display: none;
                    z-index: 1000;
                    font-weight: bold;
                }
                #yt-progress {
                    display: none;
                    margin-top: 10px;
                }
                #yt-progress-bar {
                    height: 5px;
                    background: #ddd;
                    border-radius: 3px;
                    overflow: hidden;
                }
                #yt-progress-bar > div {
                    height: 100%;
                    width: 0%;
                    background: var(--yt-red);
                    transition: width 0.3s ease;
                }
                #yt-progress-text {
                    font-size: 12px;
                    margin-top: 5px;
                    color: #666;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="before-unload-message">
                Идет загрузка файла! Если вы закроете страницу, загрузка прервется.
            </div>
            
            <div class="header">Telegram-like Chat + YouTube Downloader</div>
            
            <div class="download-section">
                <h3 style="margin-top:0; color:var(--yt-red);">YouTube Downloader</h3>
                <input type="text" id="youtube-url" class="download-input" placeholder="Вставьте ссылку на YouTube видео">
                <button class="download-btn" onclick="downloadYouTubeVideo()">
                    <span style="font-weight:bold;">Скачать видео</span>
                </button>
                <div id="yt-progress">
                    <div id="yt-progress-bar"><div></div></div>
                    <div id="yt-progress-text">Подготовка к загрузке...</div>
                </div>
            </div>

            <div class="chat-container" id="chat">
                {% for msg in messages %}
                    {% if msg.type == 'text' %}
                        <div class="message text-message">
                            {{ msg.content }}
                            <div class="message-time">{{ msg.time }}</div>
                        </div>
                    {% else %}
                        <div class="message file-message">
                            <div class="file-info">
                                <span class="file-icon">📎</span>
                                <a href="/uploads/{{ msg.filename }}" download>{{ msg.filename }}</a>
                            </div>
                            <div class="message-time">{{ msg.time }} • {{ (msg.size/1024)|round(2) }} KB</div>
                        </div>
                    {% endif %}
                {% endfor %}
            </div>

            <div class="input-area">
                <button class="attach-btn" onclick="document.getElementById('file-input').click()">📎</button>
                <input type="file" id="file-input">
                
                <form id="text-form" style="flex:1; display:flex;">
                    <input type="text" class="text-input" id="message-input" placeholder="Введите сообщение...">
                    <button type="submit" class="send-btn">➤</button>
                </form>
            </div>

            <div id="progress-container">
                <div id="progress-bar">
                    <div id="progress"></div>
                </div>
                <div id="progress-info">
                    <span id="loaded">0 KB</span>
                    <span id="speed">0 MB/s</span>
                    <span id="total">0 KB</span>
                </div>
            </div>

            <script>
                let isDownloading = false;
                let lastLoaded = 0;
                let lastTime = 0;
                let speed = 0;
                
                function formatSpeed(bytesPerSecond) {
                    if (bytesPerSecond < 1024) return bytesPerSecond.toFixed(1) + ' B/s';
                    if (bytesPerSecond < 1024*1024) return (bytesPerSecond/1024).toFixed(1) + ' KB/s';
                    return (bytesPerSecond/(1024*1024)).toFixed(1) + ' MB/s';
                }

                window.addEventListener('beforeunload', function(e) {
                    if (isDownloading) {
                        e.preventDefault();
                        e.returnValue = 'Идет загрузка файла! Вы уверены, что хотите уйти?';
                        document.getElementById('before-unload-message').style.display = 'block';
                    }
                });

                function setDownloading(status) {
                    isDownloading = status;
                    document.getElementById('before-unload-message').style.display = status ? 'block' : 'none';
                    if (!status) {
                        document.getElementById('progress').style.width = '0%';
                        document.getElementById('yt-progress-bar').firstChild.style.width = '0%';
                    }
                }

                function uploadFile(file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const xhr = new XMLHttpRequest();
                    const progressContainer = document.getElementById('progress-container');
                    const progressBar = document.getElementById('progress');
                    const loadedSpan = document.getElementById('loaded');
                    const totalSpan = document.getElementById('total');
                    const speedSpan = document.getElementById('speed');

                    xhr.upload.onprogress = function(event) {
                        if (event.lengthComputable) {
                            const now = Date.now();
                            const loadedDiff = event.loaded - lastLoaded;
                            const timeDiff = (now - lastTime) / 1000;
                            
                            if (timeDiff > 0) {
                                speed = loadedDiff / timeDiff;
                                speedSpan.textContent = formatSpeed(speed);
                            }
                            
                            lastLoaded = event.loaded;
                            lastTime = now;
                            
                            const percent = (event.loaded / event.total) * 100;
                            progressBar.style.width = percent + '%';
                            loadedSpan.textContent = Math.round(event.loaded / 1024) + ' KB';
                            totalSpan.textContent = Math.round(event.total / 1024) + ' KB';
                        }
                    };

                    xhr.onloadstart = function() {
                        setDownloading(true);
                        lastLoaded = 0;
                        lastTime = Date.now();
                        progressContainer.style.display = 'block';
                    };

                    xhr.onload = function() {
                        if (xhr.status === 200) {
                            location.reload();
                        } else {
                            alert('Ошибка загрузки: ' + xhr.responseText);
                        }
                        progressContainer.style.display = 'none';
                        setDownloading(false);
                    };

                    xhr.onerror = function() {
                        alert('Ошибка сети');
                        progressContainer.style.display = 'none';
                        setDownloading(false);
                    };

                    xhr.open('POST', '/upload_file', true);
                    xhr.send(formData);
                }

                function downloadYouTubeVideo() {
                    const url = document.getElementById('youtube-url').value.trim();
                    if (!url) {
                        alert('Введите ссылку на YouTube видео');
                        return;
                    }

                    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                        alert('Пожалуйста, введите корректную ссылку на YouTube видео');
                        return;
                    }

                    setDownloading(true);
                    const progressBar = document.getElementById('yt-progress-bar').firstChild;
                    const progressText = document.getElementById('yt-progress-text');
                    const ytProgress = document.getElementById('yt-progress');
                    
                    ytProgress.style.display = 'block';
                    progressText.textContent = 'Начинаем загрузку...';
                    
                    fetch('/download_youtube', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ url: url })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            progressBar.style.width = '100%';
                            progressText.textContent = 'Загрузка завершена! Скачивание начнется автоматически...';
                            
                            setTimeout(() => {
                                const a = document.createElement('a');
                                a.href = `/youtube_downloads/${encodeURIComponent(data.filename)}`;
                                a.download = data.filename;
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                
                                setTimeout(() => {
                                    ytProgress.style.display = 'none';
                                    progressBar.style.width = '0%';
                                    document.getElementById('youtube-url').value = '';
                                }, 3000);
                            }, 1000);
                        } else {
                            alert('Ошибка: ' + data.error);
                            progressText.textContent = 'Ошибка: ' + data.error;
                        }
                        setDownloading(false);
                    })
                    .catch(error => {
                        alert('Ошибка: ' + error);
                        progressText.textContent = 'Ошибка: ' + error;
                        setDownloading(false);
                    });

                    let progress = 0;
                    const interval = setInterval(() => {
                        if (!isDownloading) {
                            clearInterval(interval);
                            return;
                        }
                        
                        progress += 1 + Math.random() * 4;
                        if (progress >= 95) {
                            progress = 95;
                            clearInterval(interval);
                        }
                        progressBar.style.width = progress + '%';
                        progressText.textContent = `Загружено: ${Math.round(progress)}% (${formatSpeed(speed)})`;
                    }, 500);
                }

                document.getElementById('file-input').addEventListener('change', function(e) {
                    if (this.files.length > 0) {
                        uploadFile(this.files[0]);
                    }
                });

                document.getElementById('text-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    const input = document.getElementById('message-input');
                    if (input.value.trim() !== '') {
                        fetch('/save_text', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: 'text=' + encodeURIComponent(input.value)
                        }).then(response => {
                            if (response.ok) {
                                location.reload();
                            } else {
                                alert('Ошибка отправки сообщения');
                            }
                        });
                        input.value = '';
                    }
                });

                const chat = document.getElementById('chat');
                chat.scrollTop = chat.scrollHeight;
            </script>
        </body>
    </html>
    """, messages=messages)

def save_text(text, filename=None):
    try:
        if not filename:
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"text_{current_time}.txt"
        else:
            filename = sanitize_filename(filename) + ".txt"

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)
        
        logger.info(f"Текст сохранён в файл: {file_path}")
        return filename
    except Exception as e:
        logger.error(f"Ошибка при записи в файл: {e}")
        return None

@app.route('/save_text', methods=['POST'])
def save_text_request():
    text = request.form['text']
    filename = save_text(text)
    if filename:
        return jsonify(success=True)
    return jsonify(error="Ошибка сохранения"), 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify(error="Файл не выбран"), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify(error="Неверное имя файла"), 400

        filename = sanitize_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Файл успешно загружен: {filename}")
        return jsonify(success=True)
    
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {str(e)}")
        return jsonify(error=str(e)), 500

@app.route('/download_youtube', methods=['POST'])
def download_youtube():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify(error="URL не указан"), 400

        client_info = get_client_info()
        logger.info(f"Начало загрузки YouTube видео: {url} для клиента {client_info}")

        yt = pytube.YouTube(url)
        stream = yt.streams.get_highest_resolution()
        
        safe_title = sanitize_filename(yt.title)
        filename = f"{safe_title}.mp4"
        filepath = os.path.join(app.config['YT_DOWNLOAD_FOLDER'], filename)
        
        active_downloads[filename] = {
            'start_time': datetime.now(),
            'client': client_info,
            'url': url
        }
        
        stream.download(output_path=app.config['YT_DOWNLOAD_FOLDER'], filename=filename)
        
        active_downloads.pop(filename, None)
        
        logger.info(f"Видео успешно загружено: {filename}")
        return jsonify(success=True, filename=filename)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки YouTube видео: {str(e)}")
        return jsonify(error=str(e)), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/youtube_downloads/<filename>')
def serve_youtube_download(filename):
    try:
        return send_from_directory(app.config['YT_DOWNLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)