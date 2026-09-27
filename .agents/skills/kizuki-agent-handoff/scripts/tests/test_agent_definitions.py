"""Check the executable configuration contract, not instruction prose."""

import json
from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[5]


class AgentDefinitionsTest(unittest.TestCase):
    def test_required_fields_only_and_matching_hook(self):
        definitions = sorted((ROOT / ".codex/agents").glob("*.toml"))
        self.assertTrue(definitions)
        hooks = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
        matchers = [entry["matcher"] for entry in hooks["hooks"]["SubagentStop"]]
        names = set()
        for path in definitions:
            with self.subTest(path=path.name):
                data = tomllib.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(set(data), {"name", "description", "developer_instructions"})
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in data.values()))
                self.assertEqual(data["name"], path.stem)
                self.assertNotIn(data["name"], names)
                names.add(data["name"])
                self.assertTrue(any(re.fullmatch(matcher, data["name"]) for matcher in matchers))
        for unrelated in ("default", "worker", "explorer", "not-a-kizuki-agent"):
            self.assertFalse(any(re.search(matcher, unrelated) for matcher in matchers))


if __name__ == "__main__":
    unittest.main()
