from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import helpers


FIXTURE = Path(__file__).parent / "assets" / "prd-to-spec"


class ConditionalRoutingV2Test(unittest.TestCase):
    """Black-box coverage for workflow schema v2 at the CLI process seam."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.project = self.root / "project"
        self.home = self.root / "home"
        self.project.mkdir()
        self.home.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.project)], check=True)

    def install(self, alias: str, definition: str) -> Path:
        package = self.home / ".agents" / "workflows" / alias
        package.mkdir(parents=True, exist_ok=True)
        (package / "workflow.yaml").write_text(definition, encoding="utf-8")
        return package

    def command(self, *args: str, env: dict[str, str] | None = None):
        return helpers.run_wf(
            *args,
            cwd=self.project,
            env={
                **os.environ,
                "HOME": str(self.home),
                **(env or {}),
            },
        )

    def start(self, alias: str, *variables: str, title: str = "Validate conditional routing"):
        return self.command("start", alias, "--task", title, *variables)

    def next(self):
        return self.command("next")

    def state(self):
        runtime = self.project / ".workflow-harness"
        pointer = json.loads((runtime / "task.json").read_text(encoding="utf-8"))
        task_id = pointer["task_id"]
        return json.loads(
            (runtime / "tasks" / task_id / "state.json").read_text(encoding="utf-8")
        )

    def history(self):
        runtime = self.project / ".workflow-harness"
        pointer = json.loads((runtime / "task.json").read_text(encoding="utf-8"))
        history = runtime / "tasks" / pointer["task_id"] / "history.jsonl"
        if not history.exists() and not (runtime / "task.json").exists():
            history = None
        return [
            json.loads(line)
            for line in history.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def assert_payload(self, completed, status: str) -> dict[str, object]:
        payload = json.loads(completed.stdout or "{}")
        self.assertEqual(payload["status"], status, json.dumps(payload, ensure_ascii=False))
        return payload

    def test_validate_reports_a_valid_v2_package_without_task_side_effects(self) -> None:
        self.install(
            "minimal",
            """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read and think.
    gates: []
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
""",
        )
        completed = self.command("validate", "minimal")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout),
            {"status": "valid", "alias": "minimal"},
        )
        self.assertFalse((self.project / ".workflow-harness").exists())

    def test_validate_rejects_v1_transitions_with_bounded_syntax_reason(self) -> None:
        definition = """
version: v1
entry: design
terminal: done
steps:
  design: {title: Design, guide: Read and think., gates: []}
  done: {title: Done, guide: null}
transitions:
  - {from: design, to: done}
"""
        self.install("legacy", definition)
        completed = self.command("validate", "legacy")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        payload = self.assert_payload(completed, "invalid")
        self.assertIn("must be v2", str(payload["reason"]))
        self.assertFalse((self.project / ".workflow-harness").exists())

    def test_start_variables_are_immutable_inputs_and_resume_exact(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates:
      - {id: evidence, type: file_exists, path: docs/evidence.md}
    transitions:
      - to: confirmed
        when: entry_mode == confirmed_prd
      - to: done
        default: true
  confirmed:
    title: Confirmed
    guide: Confirmed path.
    gates: []
    transitions:
      - to: done
        default: true
  done:
    title: Done
    guide: null
"""
        self.install("mode", definition)
        completed = self.start("mode", "--var", "entry_mode=confirmed_prd")
        self.assertEqual(completed.returncode, 0)
        state = self.state()
        self.assertEqual(state["inputs"], {"entry_mode": "confirmed_prd"})
        self.assertEqual(state["schema"], "agent-workflow-harness.task-state.v2")
        self.assertEqual(state["visited_steps"], ["design"])

        resumed = self.start("mode", "--var", "entry_mode=confirmed_prd")
        self.assertEqual(json.loads(resumed.stdout)["status"], "active")
        changed = self.start("mode", "--var", "entry_mode=ordinary_prd")
        self.assert_payload(changed, "conflict")
        self.assertEqual(state, self.state())

    def test_duplicate_start_variables_are_an_error(self) -> None:
        self.install(
            "duplicate",
            """
version: v2
entry: design
terminal: done
steps:
  design: {title: Design, guide: Read., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
""",
        )
        completed = self.start(
            "duplicate",
            "--var", "entry_mode=confirmed_prd",
            "--var", "entry_mode=ordinary_prd",
        )
        self.assert_payload(completed, "error")
        self.assertIn("Duplicate start variable", str(json.loads(completed.stdout)["reason"]))
        self.assertFalse((self.project / ".workflow-harness").exists())

    def test_exact_string_route_and_selected_edge_history(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    transitions:
      - to: ordinary
        when: entry_mode == ordinary_prd
      - to: confirmed
        when: entry_mode == confirmed_prd
      - to: done
        default: true
  ordinary:
    title: Ordinary
    guide: Ordinary path.
    gates: []
    transitions: [{to: done, default: true}]
  confirmed:
    title: Confirmed
    guide: Confirmed path.
    gates: []
    transitions: [{to: done, default: true}]
  done: {title: Done, guide: null}
"""
        self.install("exact", definition)
        self.start("exact", "--var", "entry_mode=confirmed_prd")
        completed = self.next()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["instruction"], "Confirmed path.")
        success = self.history()[-1]
        self.assertEqual(
            success,
            {
                "event": "success",
                "from_step": "design",
                "to_step": "confirmed",
                "condition_variable": "entry_mode",
                "condition_value": "confirmed_prd",
                "resolve_source": "start_input",
                "timestamp": success["timestamp"],
            },
        )

    def test_unresolved_condition_preserves_state(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    transitions:
      - to: alternatives
        when: mode == confirmed
      - to: done
        default: true
  alternatives: {title: Alternatives, guide: Alternatives., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
"""
        self.install("unresolved", definition)
        completed = self.start("unresolved")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        before = self.state()
        continued = self.next()
        self.assert_payload(continued, "error")
        self.assertIn("unresolved", str(json.loads(continued.stdout)["reason"]))
        self.assertEqual(self.state(), before)

    def test_multiple_matching_routes_preserve_state(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    transitions:
      - to: one
        when: mode == confirmed
      - to: two
        when: alternate == confirmed
      - to: done
        default: true
  one: {title: One, guide: One., transitions: [{to: done, default: true}]}
  two: {title: Two, guide: Two., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
"""
        self.install("ambiguous", definition)
        completed = self.start(
            "ambiguous",
            "--var", "mode=confirmed",
            "--var", "alternate=confirmed",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        before = self.state()
        continued = self.next()
        self.assert_payload(continued, "error")
        self.assertIn("multiple", str(json.loads(continued.stdout)["reason"]))
        self.assertEqual(self.state(), before)

    def test_workflow_script_producer_and_environment_fallback(self) -> None:
        package = self.install(
            "producer",
            """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    condition_producers:
      mode:
        type: workflow_script
        script: scripts/mode.py
        project_args:
          - evidence/mode.txt
    transitions:
      - to: conditional
        when: mode == needs_contract
      - to: done
        default: true
  conditional: {title: Conditional, guide: Contract., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
""",
        )
        script = package / "scripts" / "mode.py"
        script.parent.mkdir()
        script.write_text(
            "from pathlib import Path\nprint(Path('evidence/mode.txt').read_text().strip())\n",
            encoding="utf-8",
        )
        evidence = self.project / "evidence" / "mode.txt"
        evidence.parent.mkdir()
        evidence.write_text("needs_contract\n", encoding="utf-8")
        self.start("producer")
        completed = self.next()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["instruction"], "Contract.")
        state = self.state()
        self.assertEqual(state["facts"]["mode"]["value"], "needs_contract")
        self.assertEqual(state["facts"]["mode"]["producing_step"], "design")

    def test_environment_alias_resolves_before_default_and_is_not_persisted(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    transitions:
      - to: overridden
        when: mode == confirmed
      - to: done
        default: true
  overridden: {title: Overridden, guide: Override., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
"""
        self.install("env-route", definition)
        self.start("env-route")
        completed = self.command("next", env={"WF_MODE": "confirmed"})
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["instruction"], "Override.")
        self.assertEqual(self.state()["facts"], {})
        self.assertEqual(self.history()[-1]["resolve_source"], "environment")

    def test_invalid_graphs_are_bounded_authoring_errors(self) -> None:
        cases = {
            "both": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions:\n"
                "      - {to: done, when: mode == true, default: true}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "duplicate-target": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions:\n"
                "      - {to: done, when: a == true}\n"
                "      - {to: done, when: b == true}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "unreachable": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions: [{to: done, default: true}]\n"
                "  orphan: {title: Orphan, guide: Orphan., transitions: [{to: done, default: true}]}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "no-terminal-path": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions: [{to: loop_end, default: true}]\n"
                "  loop_end: {title: Loop, guide: Loop., transitions: [{to: design, default: true}]}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "unsafe-producer": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    condition_producers:\n"
                "      mode: {type: workflow_script, script: ../mode.py}\n"
                "    transitions: [{to: done, when: mode == true}]\n"
                "  done: {title: Done, guide: null }\n"
            ),
            "unsupported-operator": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions:\n"
                "      - {to: done, when: \"mode != done\"}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "multiple-defaults": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions:\n"
                "      - {to: one, default: true}\n"
                "      - {to: done, default: true}\n"
                "  one: {title: One, guide: One., transitions: [{to: done, default: true}]}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "literal-whitespace": (
                "version: v2\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions:\n"
                "      - {to: done, when: \"mode == done \"}\n"
                "  done: {title: Done, guide: null}\n"
            ),
            "invalid-timeout": (
                "version: v2\n"
                "producer_timeout_seconds: 0\n"
                "entry: design\n"
                "terminal: done\n"
                "steps:\n"
                "  design:\n"
                "    title: Design\n"
                "    guide: Read.\n"
                "    transitions: [{to: done, default: true}]\n"
                "  done: {title: Done, guide: null}\n"
            ),
        }
        for alias, definition in cases.items():
            with self.subTest(case=alias):
                self.install(alias, definition)
                completed = self.command("validate", alias)
                self.assertEqual(completed.returncode, 1)
                payload = self.assert_payload(completed, "invalid")
                self.assertLessEqual(len(str(payload["reason"])), 1000)

    def test_boolean_start_input_is_normalized_at_comparison_only(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    transitions:
      - to: ready_step
        when: ready == true
      - to: done
        default: true
  ready_step: {title: Is ready, guide: Yes., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
"""
        self.install("boolean-input", definition)
        self.start("boolean-input", "--var", "ready=true")
        completed = self.next()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["instruction"], "Yes.")
        self.assertEqual(self.state()["inputs"]["ready"], "true")
        self.assertEqual(self.history()[-1]["condition_value"], "true")

    def test_producer_timeout_is_an_operational_error(self) -> None:
        package = self.install(
            "slow-producer",
            """
version: v2
producer_timeout_seconds: 1
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    condition_producers:
      ready:
        type: workflow_script
        script: scripts/slow.py
        project_args: []
    transitions:
      - to: ready
        when: ready == true
      - to: done
        default: true
  ready: {title: Ready, guide: Ready., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
""",
        )
        script = package / "scripts" / "slow.py"
        script.parent.mkdir()
        script.write_text(
            "import time\ntime.sleep(3)\nprint('true')\n",
            encoding="utf-8",
        )
        self.start("slow-producer")
        before = self.state()
        completed = self.next()
        self.assert_payload(completed, "error")
        self.assertEqual(json.loads(completed.stdout)["reason"], "Condition producer timed out for ready")
        self.assertEqual(self.state(), before)

    def test_a_step_can_resolve_multiple_local_producers(self) -> None:
        package = self.install(
            "two-producers",
            """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    condition_producers:
      mode:
        type: workflow_script
        script: scripts/mode.py
      alternate:
        type: workflow_script
        script: scripts/alternate.py
    transitions:
      - to: left
        when: mode == left
      - to: right
        when: alternate == right
      - to: done
        default: true
  left: {title: Left, guide: Left., transitions: [{to: done, default: true}]}
  right: {title: Right, guide: Right., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
""",
        )
        scripts = package / "scripts"
        scripts.mkdir()
        (scripts / "mode.py").write_text("print('left')\n", encoding="utf-8")
        (scripts / "alternate.py").write_text("print('other')\n", encoding="utf-8")
        self.start("two-producers")
        completed = self.next()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["instruction"], "Left.")
        facts = self.state()["facts"]
        self.assertEqual(facts["mode"]["value"], "left")
        self.assertEqual(facts["alternate"]["value"], "other")

    def test_command_producer_and_invalid_workflow_script_results(self) -> None:
        definition = """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    condition_producers:
      ready:
        type: command
        command: test -f docs/ready.md
    transitions:
      - to: conditional
        when: ready == true
      - to: done
        default: true
  conditional: {title: Conditional, guide: Ready., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
"""
        self.install("command", definition)
        (self.project / "docs").mkdir()
        (self.project / "docs" / "ready.md").write_text("ready\n", encoding="utf-8")
        self.start("command")
        completed = self.next()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["instruction"], "Ready.")
        self.assertEqual(self.state()["facts"]["ready"], {"value": True, "producing_step": "design", "producer_type": "command", "producer_ref": "test -f docs/ready.md"})

    def test_producer_failure_is_an_error_and_does_not_change_state(self) -> None:
        package = self.install(
            "bad-producer",
            """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates: []
    condition_producers:
      mode:
        type: workflow_script
        script: scripts/mode.py
        project_args: []
    transitions:
      - to: conditional
        when: mode == true
      - to: done
        default: true
  conditional: {title: Conditional, guide: Bad., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
""",
        )
        script = package / "scripts" / "mode.py"
        script.parent.mkdir()
        script.write_text("print('true\\nextra')\n", encoding="utf-8")
        self.start("bad-producer")
        before = self.state()
        completed = self.next()
        self.assert_payload(completed, "error")
        self.assertEqual(json.loads(completed.stdout)["reason"], "Condition producer mode must emit one scalar line")
        self.assertEqual(self.state(), before)

    def test_fixture_routes_entry_mode_producer_and_backedge_limit(self) -> None:
        package = self.home / ".agents" / "workflows" / "prd-to-spec"
        shutil.copytree(FIXTURE, package)
        self.start("prd-to-spec", "--var", "entry_mode=confirmed_prd")
        evidence = self.project / "evidence"
        evidence.mkdir()
        (evidence / "contract.txt").write_text("cross-application\n", encoding="utf-8")
        (evidence / "routing.txt").write_text("incomplete\n", encoding="utf-8")

        self.assert_payload(self.next(), "active")  # architecture_split -> confirmed_prd
        self.assert_payload(self.next(), "active")  # confirmed_prd -> technical_contract
        self.assert_payload(self.next(), "active")  # technical_contract -> contract_clarification
        self.assert_payload(self.next(), "active")  # -> routing_gap and producer records true
        first_backedge = self.next()
        self.assert_payload(first_backedge, "active")
        self.assertEqual(self.state()["backedge_counts"]["routing_gap"]["architecture_split"], 1)

        for expected_count in (2, 3):
            self.assert_payload(self.next(), "active")  # architecture -> confirmed
            self.assert_payload(self.next(), "active")  # confirmed -> technical
            self.assert_payload(self.next(), "active")  # technical -> clarification
            self.assert_payload(self.next(), "active")  # clarification -> routing gap
            self.assert_payload(self.next(), "active")  # routing gap -> architecture
            self.assertEqual(
                self.state()["backedge_counts"]["routing_gap"]["architecture_split"],
                expected_count,
            )

        # Arrive at the exhausted edge and prove the fourth attempt is atomic-error.
        self.assert_payload(self.next(), "active")  # architecture -> confirmed
        self.assert_payload(self.next(), "active")  # confirmed -> technical
        self.assert_payload(self.next(), "active")  # technical -> clarification
        self.assert_payload(self.next(), "active")  # clarification -> routing gap
        before = self.state()
        fourth = self.next()
        self.assert_payload(fourth, "error")
        self.assertIn("three", str(json.loads(fourth.stdout)["reason"]))
        self.assertEqual(self.state(), before)

    def test_fixture_can_repair_the_route_and_finish(self) -> None:
        package = self.home / ".agents" / "workflows" / "prd-to-spec"
        shutil.copytree(FIXTURE, package)
        self.start("prd-to-spec", "--var", "entry_mode=ordinary_prd")
        evidence = self.project / "evidence"
        evidence.mkdir()
        (evidence / "contract.txt").write_text("	internal\n", encoding="utf-8")
        (evidence / "routing.txt").write_text("incomplete\n", encoding="utf-8")
        self.assert_payload(self.next(), "active")  # -> technical_contract
        self.assert_payload(self.next(), "active")  # -> routing_gap
        self.assert_payload(self.next(), "active")  # -> architecture_split
        (evidence / "contract.txt").write_text("internal\n", encoding="utf-8")
        (evidence / "routing.txt").write_text("complete\n", encoding="utf-8")
        self.assert_payload(self.next(), "active")  # -> technical_contract
        self.assert_payload(self.next(), "active")  # -> routing_gap
        completed = self.next()
        self.assert_payload(completed, "done")
        self.assertFalse((self.project / ".workflow-harness" / "task.json").exists())

    def test_project_local_package_validate_uses_source_backed_workflow(self) -> None:
        package = self.project / ".agents" / "workflows" / "local-only"
        package.mkdir(parents=True)
        (package / "workflow.yaml").write_text(
            """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    transitions: [{to: done, default: true}]
  done: {title: Done, guide: null}
""",
            encoding="utf-8",
        )
        completed = self.command("validate", "local-only")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout), {"status": "valid", "alias": "local-only"})

    def test_file_exists_gate_paths_stay_inside_the_project(self) -> None:
        cases = {
            "traversal": "../outside.md",
            "absolute": "/tmp/outside.md",
            "windows": "C:/tmp/outside.md",
            "backslash": "docs\\outside.md",
        }
        for alias, bad_path in cases.items():
            with self.subTest(case=alias):
                package = self.home / ".agents" / "workflows" / alias
                package.mkdir(parents=True, exist_ok=True)
                (package / "workflow.yaml").write_text(
                    f"""
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    gates:
      - id: evidence
        type: file_exists
        path: {bad_path}
    transitions: [{{to: done, default: true}}]
  done: {{title: Done, guide: null}}
""",
                    encoding="utf-8",
                )
                completed = self.command("validate", alias)
                self.assertEqual(completed.returncode, 1)
                payload = self.assert_payload(completed, "invalid")
                self.assertIn("unsafe path", str(payload["reason"]))
                self.assertFalse((self.project / ".workflow-harness").exists())

    def test_runtime_fact_state_rejects_malformed_provenance(self) -> None:
        self.install(
            "fact-state",
            """
version: v2
entry: design
terminal: done
steps:
  design:
    title: Design
    guide: Read.
    transitions: [{to: done, default: true}]
  done: {title: Done, guide: null}
""",
        )
        self.start("fact-state")
        state_path = self.project / ".workflow-harness" / "task.json"
        pointer = json.loads(state_path.read_text(encoding="utf-8"))
        state_file = self.project / ".workflow-harness" / "tasks" / pointer["task_id"] / "state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["facts"] = {
            "bad name": {
                "value": "x",
                "producing_step": "design",
                "producer_type": "workflow_script",
                "producer_ref": "scripts/x.py",
            }
        }
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        completed = self.next()
        self.assert_payload(completed, "error")
        self.assertEqual(
            json.loads(completed.stdout)["reason"],
            "Active workflow task state is invalid or unreadable",
        )

    def test_old_v1_task_state_is_not_migrated(self) -> None:
        self.install(
            "new-v2",
            """
version: v2
entry: design
terminal: done
steps:
  design: {title: Design, guide: Read., transitions: [{to: done, default: true}]}
  done: {title: Done, guide: null}
""",
        )
        completed = self.start("new-v2")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        state_path = self.project / ".workflow-harness"
        pointer = json.loads((state_path / "task.json").read_text(encoding="utf-8"))
        state_file = state_path / "tasks" / pointer["task_id"] / "state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["schema"] = "agent-workflow-harness.task-state.v1"
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        continued = self.next()
        self.assert_payload(continued, "error")
        self.assertIn("workflow v1 state is not supported", str(json.loads(continued.stdout)["reason"]))


if __name__ == "__main__":
    unittest.main()
