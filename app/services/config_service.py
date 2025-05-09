# app/services/config_service.py
import json
import os

CONFIG_FILE = "app_config.json"

def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {"copy_to_clipboard": True}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)