# app/core/utils.py
import socket
import re
from user_agents import parse

def get_client_info(request):
    user_agent = parse(request.headers.get('User-Agent', ''))
    client_ip = request.remote_addr or 'unknown'
    
    try:
        hostname = socket.gethostbyaddr(client_ip)[0]
    except (socket.herror, socket.gaierror):
        hostname = 'unknown'
    
    return {
        'ip': client_ip,
        'platform': user_agent.os.family,
        'browser': user_agent.browser.family,
        'device': user_agent.device.family,
        'hostname': hostname
    }

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()[:255]