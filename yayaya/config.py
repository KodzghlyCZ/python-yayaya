import yaml
import os

_config = None
_config_path = None
CONFIG_PATH = "config.yaml"  # Default config path

def _load(path):
    global _config, _config_path
    full_path = os.path.abspath(path)
    with open(full_path, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)
    _config_path = full_path

# Load immediately at import
_load(CONFIG_PATH)

def get(key, default=None):
    if _config is None:
        raise RuntimeError("Config not loaded.")
    value = _config
    for part in key.split("."):
        value = value.get(part, default) if isinstance(value, dict) else default
    return value

def reload_config():
    if _config_path is None:
        raise RuntimeError("Config path unknown.")
    _load(_config_path)

def override_config_path(path):
    _load(path)
