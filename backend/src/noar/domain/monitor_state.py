from dataclasses import dataclass, replace

from noar.domain.enums import MonitorState


@dataclass(frozen=True)
class MonitorSnapshot:
    """Just the fields of a monitor the state machine needs to decide a transition."""

    state: MonitorState
    consecutive_failures: int
    consecutive_successes: int
    fail_threshold: int


@dataclass(frozen=True)
class CheckEvaluation:
    snapshot: MonitorSnapshot
    opened_incident: bool
    closed_incident: bool


def evaluate_check(snapshot: MonitorSnapshot, success: bool) -> CheckEvaluation:
    """Apply one check result to a monitor snapshot and decide state transitions.

    A paused monitor never reacts to check results. Recovery closes an incident
    on the first success after a failure streak; opening an incident requires
    `fail_threshold` consecutive failures, so isolated blips don't trip it.
    """
    if snapshot.state is MonitorState.PAUSED:
        return CheckEvaluation(snapshot=snapshot, opened_incident=False, closed_incident=False)

    if success:
        closed_incident = snapshot.state is MonitorState.DOWN
        new_snapshot = replace(
            snapshot,
            state=MonitorState.UP,
            consecutive_failures=0,
            consecutive_successes=snapshot.consecutive_successes + 1,
        )
        return CheckEvaluation(
            snapshot=new_snapshot, opened_incident=False, closed_incident=closed_incident
        )

    consecutive_failures = snapshot.consecutive_failures + 1
    opened_incident = (
        consecutive_failures >= snapshot.fail_threshold and snapshot.state is not MonitorState.DOWN
    )
    new_state = MonitorState.DOWN if opened_incident else snapshot.state
    new_snapshot = replace(
        snapshot,
        state=new_state,
        consecutive_failures=consecutive_failures,
        consecutive_successes=0,
    )
    return CheckEvaluation(
        snapshot=new_snapshot, opened_incident=opened_incident, closed_incident=False
    )
