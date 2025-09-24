import os
from typing import Any

import yaml


class ConfigError(Exception):
    """Base class for config-related errors."""


class ConfigNotLoadedError(ConfigError):
    """Raised when config is accessed before being loaded."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when the specified config file is missing."""


class ConfigKeyNotFoundError(ConfigError):
    """Optional: Raised when a required config key is missing."""


_config = None
_config_path = None


def _load(path):
    global _config, _config_path
    full_path = os.path.abspath(path)
    if not os.path.exists(full_path):
        raise ConfigFileNotFoundError(f"Config file not found: {full_path}")
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
    except Exception as e:
        raise ConfigError(f"Failed to load config file: {e}")
    _config_path = full_path


def init(path=None):
    """Call this early in app to set config path explicitly."""
    try:
        _load(path)
    except Exception as e:
        raise ConfigError(f"Config init failed: {e}")


def _ensure_loaded():
    if _config is None:
        try:
            init()
        except Exception as e:
            raise ConfigNotLoadedError(
                "Config not initialized and fallback failed."
            ) from e


def get(key: str, default: Any = None, *, required: bool = False):
    """
    Retrieves a nested key from YAML config using dot-notation.

    - If `required=True` and the key is not found, raises ConfigKeyNotFoundError.
    - If `required=False`, returns `default` if key is not found; if no default provided,
      raises ConfigKeyNotFoundError (so callers can distinguish missing optionals).
    """
    _ensure_loaded()
    value: Any = _config
    missing = False

    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            missing = True
            break
        value = value[part]

    if missing:
        if required:
            raise ConfigKeyNotFoundError(f"Required config key missing: {key}")
        elif default is not None:
            return default
        else:
            raise ConfigKeyNotFoundError(
                f"Optional config key '{key}' not found and no default provided."
            )

    return value


def contains(key: str) -> bool:
    """Checks whether a nested key exists in the YAML config."""
    _ensure_loaded()
    value: Any = _config
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return True


def reload_config():
    if _config_path is None:
        raise ConfigNotLoadedError("Config path is unknown; cannot reload.")
    _load(_config_path)


def override_config_path(path):
    _load(path)


