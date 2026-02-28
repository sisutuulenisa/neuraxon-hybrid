#!/usr/bin/env python3
"""Read-only phase-1 sidecar observer.

Ingests task state + optional history events and emits advisory scorecards.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate read-only sidecar task advice")
    parser.add_argument(
        "--active-tasks",
        required=True,
        help="Path to active-tasks JSON (list or object with tasks key)",
    )
    parser.add_argument(
        "--events",
        help="Optional path to history events JSON (list or object with events key)",
    )
    parser.add_argument(
        "--out-latest",
        default="sidecar/out/task-advice-latest.json",
        help="Latest advisory output path",
    )
    parser.add_argument(
        "--out-timestamped-dir",
        default="sidecar/out",
        help="Directory for timestamped advisory outputs",
    )
    parser.add_argument(
        "--write-timestamped",
        action="store_true",
        help="Also write sidecar/out/task-advice-<timestamp>.json",
    )
    return parser.parse_args()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(float(raw), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    text = str(raw).strip()
    if not text:
        return None

    # ISO-8601
    iso = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    # epoch in string form
    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> int:
    return int(max(lower, min(upper, round(value))))


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_list(payload: Any, list_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in list_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _first_non_empty(task: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = task.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def _status_norm(raw: str) -> str:
    status = raw.strip().lower()
    aliases = {
        "in_progress": "running",
        "in-progress": "running",
        "queued": "pending",
        "complete": "done",
        "completed": "done",
        "success": "done",
    }
    return aliases.get(status, status or "unknown")


def _event_time(event: dict[str, Any]) -> datetime | None:
    for key in ("updatedAt", "updated_at", "timestamp", "time", "ts", "createdAt", "created_at"):
        parsed = _parse_time(event.get(key))
        if parsed is not None:
            return parsed
    return None


def _task_time(task: dict[str, Any]) -> datetime | None:
    for key in ("updatedAt", "updated_at", "lastUpdate", "last_update", "timestamp", "createdAt", "created_at"):
        parsed = _parse_time(task.get(key))
        if parsed is not None:
            return parsed
    return None


def _is_checkpoint_event(event: dict[str, Any]) -> bool:
    joined = " ".join(
        [
            str(event.get("type", "")),
            str(event.get("kind", "")),
            str(event.get("status", "")),
            str(event.get("note", "")),
            str(event.get("message", "")),
        ]
    ).lower()
    return "checkpoint" in joined


def _is_artifact_event(event: dict[str, Any]) -> bool:
    joined = " ".join(
        [
            str(event.get("type", "")),
            str(event.get("kind", "")),
            str(event.get("status", "")),
            str(event.get("note", "")),
            str(event.get("message", "")),
        ]
    ).lower()
    return any(token in joined for token in ("artifact", "report", "output", "evidence"))


def _is_timeout_or_retry_event(event: dict[str, Any]) -> bool:
    joined = " ".join(
        [
            str(event.get("type", "")),
            str(event.get("kind", "")),
            str(event.get("status", "")),
            str(event.get("note", "")),
            str(event.get("message", "")),
        ]
    ).lower()
    return any(token in joined for token in ("timeout", "retry", "stale"))


def _is_blocker_event(event: dict[str, Any]) -> bool:
    joined = " ".join(
        [
            str(event.get("type", "")),
            str(event.get("kind", "")),
            str(event.get("status", "")),
            str(event.get("note", "")),
            str(event.get("message", "")),
        ]
    ).lower()
    return any(token in joined for token in ("block", "failed", "error", "needs-human"))


def _artifact_count(task: dict[str, Any], task_events: list[dict[str, Any]]) -> int:
    raw = task.get("artifact_count")
    if isinstance(raw, int) and raw >= 0:
        return raw

    artifacts = task.get("artifacts")
    if isinstance(artifacts, list):
        return len(artifacts)

    return sum(1 for event in task_events if _is_artifact_event(event))


def _retry_count(task: dict[str, Any], task_events: list[dict[str, Any]]) -> int:
    for key in ("retry_count", "retries", "retryCount"):
        raw = task.get(key)
        if isinstance(raw, int) and raw >= 0:
            return raw
        if isinstance(raw, str) and raw.isdigit():
            return int(raw)

    return sum(1 for event in task_events if _is_timeout_or_retry_event(event))


def _has_test_output(task: dict[str, Any], task_events: list[dict[str, Any]]) -> bool:
    explicit = task.get("has_test_output")
    if isinstance(explicit, bool):
        return explicit

    tests = task.get("tests")
    if isinstance(tests, list) and len(tests) > 0:
        return True

    for event in task_events:
        joined = " ".join(
            [
                str(event.get("type", "")),
                str(event.get("kind", "")),
                str(event.get("status", "")),
                str(event.get("note", "")),
                str(event.get("message", "")),
            ]
        ).lower()
        if "test" in joined:
            return True
    return False


def _score_progress(
    status: str,
    age_minutes: float | None,
    checkpoint_age_minutes: float | None,
    artifact_count: int,
    event_count_2h: int,
) -> int:
    score = 0.0

    if status in {"done"}:
        score += 100
    elif status in {"running"}:
        score += 30
    elif status in {"pending"}:
        score += 15
    elif status in {"failed", "error", "blocked"}:
        score += 5

    if age_minutes is not None:
        if age_minutes <= 15:
            score += 25
        elif age_minutes <= 60:
            score += 15
        elif age_minutes <= 180:
            score += 5
        else:
            score -= 15

    if checkpoint_age_minutes is not None:
        if checkpoint_age_minutes <= 15:
            score += 20
        elif checkpoint_age_minutes <= 60:
            score += 10
        else:
            score -= 10

    if artifact_count > 0:
        score += min(15, artifact_count * 5)

    if event_count_2h >= 3:
        score += 10
    elif event_count_2h > 0:
        score += 5

    return _clamp(score)


def _score_reliability(
    status: str,
    age_minutes: float | None,
    retry_count: int,
    blocker_events: int,
    timeout_retry_events: int,
    checkpoint_age_minutes: float | None,
) -> int:
    score = 100.0

    if status in {"failed", "error", "blocked"}:
        score -= 40

    score -= min(50, retry_count * 12)
    score -= min(20, timeout_retry_events * 5)
    score -= min(20, blocker_events * 10)

    if age_minutes is not None and age_minutes > 120:
        score -= 20

    if status == "running" and checkpoint_age_minutes is None:
        score -= 15
    elif checkpoint_age_minutes is not None and checkpoint_age_minutes > 60:
        score -= 10

    return _clamp(score)


def _score_evidence(
    status: str,
    artifact_count: int,
    has_test_output: bool,
    event_count_2h: int,
    reproducible_flag: bool | None,
) -> int:
    score = 0.0

    if artifact_count > 0:
        score += min(45, 20 + artifact_count * 5)

    if has_test_output:
        score += 25

    if reproducible_flag is True:
        score += 20

    if status == "done":
        score += 10

    if event_count_2h > 0:
        score += 5

    return _clamp(score)


def _advice_for(
    status: str,
    progress: int,
    reliability: int,
    evidence: int,
    blocker_events: int,
    retry_count: int,
    age_minutes: float | None,
) -> tuple[str, int, list[str]]:
    reasons: list[str] = []

    if status in {"failed", "error", "blocked"} or blocker_events > 0:
        reasons.append("hard blocker/status failure gedetecteerd")
        advice = "needs-human"
        confidence = 90
        return advice, confidence, reasons

    if progress < 35 and reliability < 45:
        reasons.append("lage progress + lage reliability")
        if retry_count >= 2:
            reasons.append("meerdere retries/timeouts")
        if age_minutes is not None and age_minutes > 120:
            reasons.append("task lijkt stale")
        advice = "fallback-to-sa"
        confidence = 80
        return advice, confidence, reasons

    if progress >= 70 and reliability >= 70:
        reasons.append("stabiele voortgang op recente activiteit")
        if evidence >= 50:
            reasons.append("voldoende evidence-artefacts")
        advice = "continue"
        confidence = 75
        return advice, confidence, reasons

    reasons.append("voortgang aanwezig maar niet overtuigend")
    if retry_count > 0:
        reasons.append("retry-signalen vragen bijsturing")
    if evidence < 40:
        reasons.append("evidence nog mager")
    advice = "steer"
    confidence = 65
    return advice, confidence, reasons


def _bool_or_none(raw: Any) -> bool | None:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return None


def evaluate(active_tasks: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    now = _now_utc()

    by_task_events: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        task_id = _first_non_empty(event, ("taskId", "task_id", "id", "task"))
        if not task_id:
            continue
        by_task_events.setdefault(task_id, []).append(event)

    task_results: list[dict[str, Any]] = []

    for task in active_tasks:
        task_id = _first_non_empty(task, ("taskId", "task_id", "id"), default="unknown-task")
        status = _status_norm(_first_non_empty(task, ("status", "state"), default="unknown"))
        task_events = by_task_events.get(task_id, [])

        task_updated = _task_time(task)
        event_times = [t for t in (_event_time(ev) for ev in task_events) if t is not None]
        last_event_time = max(event_times) if event_times else None

        last_update = max([t for t in [task_updated, last_event_time] if t is not None], default=None)
        age_minutes = (
            max(0.0, (now - last_update).total_seconds() / 60.0) if last_update is not None else None
        )

        checkpoint_times = [
            t
            for ev in task_events
            if _is_checkpoint_event(ev)
            for t in [_event_time(ev)]
            if t is not None
        ]
        checkpoint_age_minutes = (
            max(0.0, (now - max(checkpoint_times)).total_seconds() / 60.0)
            if checkpoint_times
            else None
        )

        event_count_2h = 0
        for event_time in event_times:
            if (now - event_time).total_seconds() <= 2 * 3600:
                event_count_2h += 1

        blocker_events = sum(1 for ev in task_events if _is_blocker_event(ev))
        timeout_retry_events = sum(1 for ev in task_events if _is_timeout_or_retry_event(ev))

        artifact_count = _artifact_count(task, task_events)
        retry_count = _retry_count(task, task_events)
        has_test_output = _has_test_output(task, task_events)
        reproducible_flag = _bool_or_none(task.get("reproducible"))

        progress = _score_progress(status, age_minutes, checkpoint_age_minutes, artifact_count, event_count_2h)
        reliability = _score_reliability(
            status,
            age_minutes,
            retry_count,
            blocker_events,
            timeout_retry_events,
            checkpoint_age_minutes,
        )
        evidence = _score_evidence(status, artifact_count, has_test_output, event_count_2h, reproducible_flag)

        advice, confidence, reasons = _advice_for(
            status,
            progress,
            reliability,
            evidence,
            blocker_events,
            retry_count,
            age_minutes,
        )

        task_results.append(
            {
                "task_id": task_id,
                "status": status,
                "scores": {
                    "progress": progress,
                    "reliability": reliability,
                    "evidence": evidence,
                },
                "advice": advice,
                "confidence": confidence,
                "reasons": reasons,
                "snapshot": {
                    "age_minutes": round(age_minutes, 1) if age_minutes is not None else None,
                    "checkpoint_age_minutes": round(checkpoint_age_minutes, 1)
                    if checkpoint_age_minutes is not None
                    else None,
                    "retry_count": retry_count,
                    "artifact_count": artifact_count,
                    "events_last_2h": event_count_2h,
                    "blocker_events": blocker_events,
                    "timeout_or_retry_events": timeout_retry_events,
                    "has_test_output": has_test_output,
                    "reproducible": reproducible_flag,
                },
            }
        )

    summary = {
        "continue": sum(1 for t in task_results if t["advice"] == "continue"),
        "steer": sum(1 for t in task_results if t["advice"] == "steer"),
        "fallback-to-sa": sum(1 for t in task_results if t["advice"] == "fallback-to-sa"),
        "needs-human": sum(1 for t in task_results if t["advice"] == "needs-human"),
    }

    return {
        "schema_version": "sidecar-advice-v1",
        "generated_at_utc": _iso_utc(now),
        "summary": summary,
        "tasks": task_results,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    args = parse_args()

    active_path = Path(args.active_tasks)
    if not active_path.exists():
        raise SystemExit(f"Missing active task input: {active_path}")

    active_payload = _load_json(active_path)
    active_tasks = _extract_list(active_payload, ("tasks", "active_tasks", "items"))

    events: list[dict[str, Any]] = []
    if args.events:
        events_path = Path(args.events)
        if not events_path.exists():
            raise SystemExit(f"Missing events input: {events_path}")
        events_payload = _load_json(events_path)
        events = _extract_list(events_payload, ("events", "history", "items"))

    output = evaluate(active_tasks, events)
    output["inputs"] = {
        "active_tasks": str(active_path),
        "events": str(Path(args.events)) if args.events else None,
        "active_task_count": len(active_tasks),
        "event_count": len(events),
    }

    latest_path = Path(args.out_latest)
    _write_json(latest_path, output)

    if args.write_timestamped:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stamped_path = Path(args.out_timestamped_dir) / f"task-advice-{stamp}.json"
        _write_json(stamped_path, output)

    print(f"Wrote advisory output: {latest_path}")
    if args.write_timestamped:
        print(f"Wrote timestamped output under: {args.out_timestamped_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
