# app/services/config_service.py
import json
import logging
import os

CONFIG_FILE = "app_config.json"

def get_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            return {"copy_to_clipboard": True}
        
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Config error: {str(e)}")
        return {"copy_to_clipboard": True}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)