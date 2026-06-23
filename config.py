import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

DEFAULT_CONFIG = {
    'gemini_api_key': '',
    'default_provider': 'Gemini',
    'gemini_model': 'gemini-3.5-flash',
    'ollama_model': 'llama3.2',
    'ollama_url': 'http://localhost:11434',
    'preset_index': 0,
    'custom_prompt': ''
}

def load_config() -> dict:
    """Loads config from config.json, merges with defaults, or returns defaults if file not found."""
    # Check if there's an environment variable for Gemini API Key first
    env_key = os.environ.get("GEMINI_API_KEY", "")
    
    config = DEFAULT_CONFIG.copy()
    if env_key:
        config['gemini_api_key'] = env_key

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                config.update(saved)
        except Exception:
            # If JSON is corrupt, fallback to defaults
            pass
            
    # Always prioritize environment variable if set and config was empty
    if env_key and not config['gemini_api_key']:
        config['gemini_api_key'] = env_key
        
    return config

def save_config(config: dict):
    """Saves the configuration to config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
