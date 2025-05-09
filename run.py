import eventlet

import app
eventlet.monkey_patch()

from app import create_app, socketio
import socket
import os
import logging

def get_local_ip():
    try:
        # Альтернативный способ получения IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logging.warning(f"Не удалось определить локальный IP: {str(e)}")
        return "127.0.0.1"

def main():
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", 8080))
    local_ip = get_local_ip()

    app = create_app()

    print("\n" + "="*50)
    print(f"Доступ в локальной сети: http://{local_ip}:{port}")
    print(f"Локальный доступ:       http://localhost:{port}")
    print("="*50 + "\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=True
    )

if __name__ == "__main__":
    main()