from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tests import helpers


class HistoryRecordTest(unittest.TestCase):
    """Runtime records must stay inspectable and timestamped."""

    def test_history_and_state_are_timestamped_and_human_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "demo-project"
            project.mkdir()
            home = root / "home"
            workflow = helpers.write_workflow(
                home,
                entry="需求澄清",
                terminal="完成",
                steps={
                    "需求澄清": {
                        "title": "需求澄清",
                        "guide": "澄清需求",
                        "gates": [helpers.file_gate("requirements", "docs/requirements.md")],
                    },
                    "完成": {"title": "完成", "guide": "结束", "gates": []},
                },
                transitions=[helpers.transition("需求澄清", "完成")],
            )
            helpers.install_source_package(home, "chinese-delivery", workflow=workflow)
            env = {**os.environ, "HOME": str(home)}

            started = helpers.run_wf(
                "start", "chinese-delivery", "--task", "Preserve readable output", cwd=project, env=env
            )
            self.assertEqual(started.returncode, 0, started.stderr)

            pointer_path = project / ".workflow-harness" / "task.json"
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            task_dir = project / ".workflow-harness" / "tasks" / str(pointer["task_id"])
            history_path = task_dir / "history.jsonl"
            state_path = task_dir / "state.json"

            blocked = helpers.run_wf("next", cwd=project, env=env)
            self.assertEqual(blocked.returncode, 1)
            (project / "docs").mkdir()
            (project / "docs" / "requirements.md").write_text("目标\n", encoding="utf-8")
            completed = helpers.run_wf("next", cwd=project, env=env)
            self.assertEqual(completed.returncode, 0, completed.stderr)

            history = history_path.read_text(encoding="utf-8")
            self.assertIn("Preserve readable output", history)
            self.assertIn("需求澄清", history)
            self.assertNotIn("\\u", history)
            events = [json.loads(line) for line in history.splitlines()]
            self.assertEqual(
                [event["event"] for event in events],
                ["started", "blocked", "success", "done"],
            )
            local_now = datetime.now().astimezone()
            for event in events:
                parsed_time = datetime.fromisoformat(str(event["timestamp"]))
                self.assertIsNotNone(parsed_time.tzinfo)
                self.assertEqual(parsed_time.utcoffset(), local_now.utcoffset())
                self.assertLessEqual(
                    abs((parsed_time - local_now).total_seconds()), 300
                )

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["schema"], "agent-workflow-harness.task-state.v2")
            self.assertEqual(state["step"], "完成")
            self.assertEqual(state["workflow_alias"], "chinese-delivery")
            self.assertEqual(state["title"], "Preserve readable output")
            self.assertRegex(str(state["workflow_yaml_sha256"]), r"^[a-f0-9]{64}$")
            self.assertNotIn("\\u", state_path.read_text(encoding="utf-8"))
            self.assertFalse(pointer_path.exists())


if __name__ == "__main__":
    unittest.main()
