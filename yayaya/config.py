from __future__ import annotations

import os
import re
from typing import Any, Mapping, Optional, Sequence, Union

import yaml

# ${VAR_NAME} — VAR_NAME matches common environment variable identifiers.
_ENV_BRACE_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

PathSpec = Union[str, os.PathLike]
PathsArg = Union[PathSpec, Sequence[PathSpec]]


class ConfigError(Exception):
    """Base class for config-related errors."""


class ConfigNotLoadedError(ConfigError):
    """Raised when config is accessed before being loaded."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when the specified config file is missing."""


class ConfigKeyNotFoundError(ConfigError):
    """Optional: Raised when a required config key is missing."""


_config = None
_config_paths: Optional[list[str]] = None


def expand_env_placeholders(value: Any, *, environ: Optional[Mapping[str, str]] = None) -> Any:
    """
    Recursively expand ``${VAR_NAME}`` placeholders in strings using the process environment.

    - Walks dicts and lists produced by ``yaml.safe_load``.
    - Leaves scalars other than ``str`` unchanged (int, float, bool, None).
    - If a referenced variable is unset, substitutes the empty string.

    Pass ``environ`` to use a custom mapping (e.g. tests); defaults to ``os.environ``.
    """
    env: Mapping[str, str] = os.environ if environ is None else environ

    def _replace_str(s: str) -> str:
        def repl(m: Any) -> str:
            v = env.get(m.group(1), "")
            return v if isinstance(v, str) else str(v)

        return _ENV_BRACE_PATTERN.sub(repl, s)

    if isinstance(value, str):
        return _replace_str(value)
    if isinstance(value, dict):
        return {k: expand_env_placeholders(v, environ=env) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env_placeholders(item, environ=env) for item in value]
    return value


def deep_merge(base: Any, override: Any) -> Any:
    """
    Deep-merge two mappings: nested dicts are merged; any other type (or dict vs scalar)
    is replaced by ``override``. Lists are not merged element-wise—they are replaced.
    """
    if isinstance(base, dict) and isinstance(override, dict):
        out = dict(base)
        for k, v in override.items():
            if k in out:
                out[k] = deep_merge(out[k], v)
            else:
                out[k] = v
        return out
    return override


def _normalize_paths(path_or_paths: PathsArg) -> list[str]:
    if isinstance(path_or_paths, (str, os.PathLike)):
        seq: Sequence[PathSpec] = (path_or_paths,)
    elif isinstance(path_or_paths, (list, tuple)):
        if not path_or_paths:
            raise ConfigError("At least one config path is required.")
        seq = path_or_paths
    else:
        raise ConfigError(
            "path must be a str/PathLike or a non-empty list/tuple of paths."
        )
    return [os.path.abspath(p) for p in seq]


def _load_raw_file(full_path: str) -> dict:
    if not os.path.exists(full_path):
        raise ConfigFileNotFoundError(f"Config file not found: {full_path}")
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception as e:
        raise ConfigError(f"Failed to load config file {full_path}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Config file must contain a YAML mapping at the root: {full_path}"
        )
    return raw


def _load(path_or_paths: PathsArg):
    global _config, _config_paths
    paths = _normalize_paths(path_or_paths)
    merged: dict = {}
    for full_path in paths:
        chunk = _load_raw_file(full_path)
        merged = deep_merge(merged, chunk)
    _config = expand_env_placeholders(merged)
    _config_paths = paths


def init(path_or_paths: PathsArg):
    """
    Load one or more YAML files and merge them left-to-right (later files override).

    Pass a single path string, a :class:`os.PathLike`, or a list/tuple of paths.
    Nested dict keys are merged; leaves and lists are replaced by the newer file.
    ``${ENV}`` expansion runs once on the merged tree.
    """
    try:
        _load(path_or_paths)
    except Exception as e:
        raise ConfigError(f"Config init failed: {e}") from e


def _ensure_loaded():
    if _config is None:
        raise ConfigNotLoadedError(
            "Config not initialized; call init(path) or init([paths...]) first."
        )


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
    if not _config_paths:
        raise ConfigNotLoadedError("Config path is unknown; cannot reload.")
    _load(_config_paths)


def override_config_path(path_or_paths: PathsArg):
    """Replace the loaded config by loading the given path(s) with the same merge rules as ``init``."""
    _load(path_or_paths)


def config_paths() -> list[str]:
    """Return absolute paths of the files last passed to ``init`` / ``override_config_path``, or []."""
    return list(_config_paths) if _config_paths else []
