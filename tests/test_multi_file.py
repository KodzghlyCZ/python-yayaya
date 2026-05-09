"""Tests for multi-file config load and deep_merge."""

import os
import tempfile
import unittest

import yayaya
from yayaya import config, deep_merge


def _reset():
    config._config = None
    config._config_paths = None


class TestDeepMerge(unittest.TestCase):
    def test_nested_merge(self):
        a = {"app": {"x": 1, "y": {"z": 2}}, "only_a": True}
        b = {"app": {"y": {"z": 9, "w": 3}, "x": 1}}
        m = deep_merge(a, b)
        self.assertEqual(m["app"]["x"], 1)
        self.assertEqual(m["app"]["y"]["z"], 9)
        self.assertEqual(m["app"]["y"]["w"], 3)
        self.assertTrue(m["only_a"])

    def test_leaf_replaced_by_scalar(self):
        self.assertEqual(deep_merge({"a": {"b": 1}}, {"a": 2}), {"a": 2})

    def test_list_replaced(self):
        self.assertEqual(deep_merge({"a": [1, 2]}, {"a": [3]}), {"a": [3]})


class TestMultiFileInit(unittest.TestCase):
    def tearDown(self):
        _reset()

    def test_later_file_overrides(self):
        base = "a:\n  b: 1\n  c:\n    d: old\n"
        over = "a:\n  c:\n    d: new\n  e: 2\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-base.yaml", delete=False, encoding="utf-8"
        ) as f1:
            f1.write(base)
            p1 = f1.name
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-over.yaml", delete=False, encoding="utf-8"
        ) as f2:
            f2.write(over)
            p2 = f2.name
        try:
            yayaya.init([p1, p2])
            self.assertEqual(yayaya.get("a.b"), 1)
            self.assertEqual(yayaya.get("a.c.d"), "new")
            self.assertEqual(yayaya.get("a.e"), 2)
            paths = yayaya.config_paths()
            self.assertEqual(len(paths), 2)
            self.assertTrue(os.path.isabs(paths[0]))
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_single_path_still_works(self):
        yaml_text = "x: 42\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_text)
            p = f.name
        try:
            yayaya.init(p)
            self.assertEqual(yayaya.get("x"), 42)
            self.assertEqual(len(yayaya.config_paths()), 1)
        finally:
            os.unlink(p)

    def test_empty_path_list_raises(self):
        with self.assertRaises(config.ConfigError):
            yayaya.init([])

    def test_reload_reloads_all(self):
        y1 = "v: 1\n"
        y2 = "v: 2\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="1.yaml", delete=False, encoding="utf-8"
        ) as f1:
            f1.write(y1)
            p1 = f1.name
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="2.yaml", delete=False, encoding="utf-8"
        ) as f2:
            f2.write(y2)
            p2 = f2.name
        try:
            yayaya.init([p1, p2])
            self.assertEqual(yayaya.get("v"), 2)
            with open(p2, "w", encoding="utf-8") as f:
                f.write("v: 99\n")
            yayaya.reload_config()
            self.assertEqual(yayaya.get("v"), 99)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_get_before_init_raises(self):
        _reset()
        with self.assertRaises(config.ConfigNotLoadedError):
            yayaya.get("anything")


if __name__ == "__main__":
    unittest.main()
