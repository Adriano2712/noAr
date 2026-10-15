from noar.domain.enums import MonitorState
from noar.domain.monitor_state import MonitorSnapshot, evaluate_check


def snapshot(
    state: MonitorState = MonitorState.UNKNOWN,
    consecutive_failures: int = 0,
    consecutive_successes: int = 0,
    fail_threshold: int = 3,
) -> MonitorSnapshot:
    return MonitorSnapshot(
        state=state,
        consecutive_failures=consecutive_failures,
        consecutive_successes=consecutive_successes,
        fail_threshold=fail_threshold,
    )


def test_first_success_moves_unknown_to_up_without_opening_incident() -> None:
    result = evaluate_check(snapshot(), success=True)

    assert result.snapshot.state is MonitorState.UP
    assert result.snapshot.consecutive_successes == 1
    assert result.opened_incident is False
    assert result.closed_incident is False


def test_failures_below_threshold_do_not_open_incident() -> None:
    result = evaluate_check(
        snapshot(state=MonitorState.UP, fail_threshold=3, consecutive_failures=1), success=False
    )

    assert result.snapshot.state is MonitorState.UP
    assert result.snapshot.consecutive_failures == 2
    assert result.opened_incident is False


def test_reaching_fail_threshold_opens_incident_and_moves_to_down() -> None:
    result = evaluate_check(
        snapshot(state=MonitorState.UP, fail_threshold=3, consecutive_failures=2), success=False
    )

    assert result.snapshot.state is MonitorState.DOWN
    assert result.snapshot.consecutive_failures == 3
    assert result.opened_incident is True


def test_further_failures_while_down_do_not_reopen_incident() -> None:
    result = evaluate_check(
        snapshot(state=MonitorState.DOWN, fail_threshold=3, consecutive_failures=5), success=False
    )

    assert result.snapshot.state is MonitorState.DOWN
    assert result.snapshot.consecutive_failures == 6
    assert result.opened_incident is False


def test_single_success_while_down_closes_incident_and_moves_to_up() -> None:
    result = evaluate_check(
        snapshot(state=MonitorState.DOWN, consecutive_failures=5), success=True
    )

    assert result.snapshot.state is MonitorState.UP
    assert result.snapshot.consecutive_failures == 0
    assert result.snapshot.consecutive_successes == 1
    assert result.closed_incident is True
    assert result.opened_incident is False


def test_success_while_up_does_not_close_incident() -> None:
    result = evaluate_check(snapshot(state=MonitorState.UP), success=True)

    assert result.closed_incident is False


def test_flapping_failures_reset_on_success_without_opening_incident() -> None:
    after_failure = evaluate_check(
        snapshot(state=MonitorState.UP, fail_threshold=3, consecutive_failures=2), success=False
    )
    assert after_failure.snapshot.state is MonitorState.DOWN

    # A monitor flapping just under the threshold never opens an incident, and a
    # success in between resets the failure streak back to zero.
    flapping = evaluate_check(
        snapshot(state=MonitorState.UP, fail_threshold=3, consecutive_failures=1), success=False
    )
    recovered = evaluate_check(flapping.snapshot, success=True)

    assert flapping.opened_incident is False
    assert recovered.snapshot.consecutive_failures == 0
    assert recovered.closed_incident is False


def test_paused_monitor_ignores_check_results() -> None:
    original = snapshot(state=MonitorState.PAUSED, consecutive_failures=1)

    failure_result = evaluate_check(original, success=False)
    success_result = evaluate_check(original, success=True)

    assert failure_result.snapshot == original
    assert failure_result.opened_incident is False
    assert success_result.snapshot == original
    assert success_result.closed_incident is False
