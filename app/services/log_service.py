# app/services/log_service.py
import logging
from flask import request
from ..core.utils import get_client_info

logger = logging.getLogger(__name__)

def log_access():
    client_info = get_client_info(request)
    logger.info(
        f"Access: IP={client_info['ip']}, "
        f"Device={client_info['device']}, "
        f"OS={client_info['platform']}, "
        f"URL={request.url}"
    )