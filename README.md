# yayaya

> *„Ja, ja, **YAML** schon wieder.“* — Every backend dev in Berlin, probably.

**yayaya** is a tiny helper for **Y**et **A**nother **YA**ml **YA**rd (look, the letters lined up and we ran with it). It loads one YAML file, lets you read nested keys with dot notation, and expands `${ENV_VAR}` placeholders so secrets can live in the environment where they belong—not committed next to your `instruction:` prompts.

No framework. No magic beans. Just `pyyaml` and the sound of your PM saying *jajaja* when you tell them config is “basically done.”

## Install

```bash
pip install yayaya
```

Or point `pip` at this repo if you live on the edge.

## Quick start

```python
from yayaya import init, get, contains

init("/path/to/config.yaml")

title = get("app.title", default="Untitled")
db_url = get("database.url", required=True)

if contains("features.experimental"):
    ...
```

## `${ENV_VAR}` expansion

After parsing YAML, all strings are walked recursively. Placeholders like `${API_KEY}` are replaced with values from `os.environ`. Missing variables become empty strings.

```yaml
# config.yaml
service:
  api_key: "${API_KEY}"
  port: 8080
```

```python
import os
from yayaya import init, get

os.environ["API_KEY"] = "secret"
init("config.yaml")
assert get("service.api_key") == "secret"
assert get("service.port") == 8080
```

You can also run expansion yourself (e.g. on a dict you built elsewhere):

```python
from yayaya import expand_env_placeholders

data = expand_env_placeholders({"x": "${HOME}"}, environ=os.environ)
```

## API

| Function | Purpose |
| -------- | ------- |
| `init(path)` | Load YAML from `path` (absolute or relative). |
| `get(key, default=None, required=False)` | Dot-path lookup (`"db.pool.size"`). |
| `contains(key)` | Whether the path exists. |
| `reload_config()` | Re-read the same file (e.g. after deploy). |
| `override_config_path(path)` | Switch file and load. |
| `expand_env_placeholders(value, environ=None)` | Recursive `${VAR}` substitution. |

Exceptions (all subclass `ConfigError`): `ConfigNotLoadedError`, `ConfigFileNotFoundError`, `ConfigKeyNotFoundError`.

## Development

```bash
pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

## License

Whatever the repo owner says—ask Karel if you’re unsure.

---

*If YAML were a conversation, **yayaya** is the part where you nod three times and actually read the file.*
