"""Tests for ${VAR} expansion in yayaya config."""

import os
import tempfile
import unittest

import yayaya
from yayaya import config


class TestExpandEnvPlaceholders(unittest.TestCase):
    def test_plain_string(self):
        env = {"FOO": "bar"}
        self.assertEqual(
            config.expand_env_placeholders("pre-${FOO}-post", environ=env),
            "pre-bar-post",
        )

    def test_nested_dict_and_list(self):
        env = {"A": "1", "B": "2"}
        data = {
            "top": "${A}",
            "nested": {"x": ["${B}", 3], "y": 4},
        }
        out = config.expand_env_placeholders(data, environ=env)
        self.assertEqual(out["top"], "1")
        self.assertEqual(out["nested"]["x"], ["2", 3])
        self.assertEqual(out["nested"]["y"], 4)

    def test_missing_variable_empty_string(self):
        self.assertEqual(
            config.expand_env_placeholders("x-${NOTSET}-y", environ={}),
            "x--y",
        )

    def test_non_string_scalars_unchanged(self):
        self.assertIsNone(config.expand_env_placeholders(None, environ={}))
        self.assertEqual(config.expand_env_placeholders(42, environ={}), 42)
        self.assertEqual(config.expand_env_placeholders(True, environ={}), True)

    def test_init_loads_expanded_values(self):
        env = {"YAYAYA_TEST_TOKEN": "secret-value"}
        yaml_text = """
app:
  token: "${YAYAYA_TEST_TOKEN}"
  count: 7
"""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(yaml_text)
            path = f.name
        try:
            old = os.environ.get("YAYAYA_TEST_TOKEN")
            os.environ["YAYAYA_TEST_TOKEN"] = env["YAYAYA_TEST_TOKEN"]
            try:
                yayaya.init(path)
                self.assertEqual(yayaya.get("app.token"), "secret-value")
                self.assertEqual(yayaya.get("app.count"), 7)
            finally:
                if old is None:
                    del os.environ["YAYAYA_TEST_TOKEN"]
                else:
                    os.environ["YAYAYA_TEST_TOKEN"] = old
                config._config = None
                config._config_paths = None
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
