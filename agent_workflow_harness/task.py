from __future__ import annotations

import json
from dataclasses import dataclass

from agent_workflow_harness.storage import atomic_write_text
from datetime import datetime, timezone
from pathlib import Path


def _event_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class Task:
    root: Path

    @property
    def state_file(self) -> Path:
        return self.root / "state.json"

    @property
    def history(self) -> Path:
        return self.root / "history.jsonl"

    def read_state(self) -> dict[str, object]:
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def write_state(self, step: str) -> None:
        state = json.loads(self.state_file.read_text(encoding="utf-8"))
        state["step"] = step
        atomic_write_text(
            self.state_file,
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        )

    def append_history(self, event: dict[str, object]) -> None:
        record = {**event, "timestamp": _event_timestamp()}
        self.root.mkdir(parents=True, exist_ok=True)
        with self.history.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def history_events(self) -> list[dict[str, object]]:
        if not self.history.exists():
            return []
        events: list[dict[str, object]] = []
        with self.history.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    def append_history_once(self, event: dict[str, object]) -> None:
        for existing in self.history_events():
            if all(existing.get(key) == value for key, value in event.items()):
                return
        self.append_history(event)

    def latest_human_decision(
        self,
        step_name: str,
        gate_id: str,
    ) -> dict[str, object] | None:
        latest: dict[str, object] | None = None
        for event in self.history_events():
            event_type = event.get("event")
            if event_type == "started" and event.get("entry") == step_name:
                latest = None
            elif event_type == "success" and event.get("to_step") == step_name:
                latest = None
            elif (
                event_type == "human_decision"
                and event.get("step") == step_name
                and event.get("gate") == gate_id
            ):
                latest = event
        return latest
