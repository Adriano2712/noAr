from enum import StrEnum


class MonitorState(StrEnum):
    UNKNOWN = "unknown"
    UP = "up"
    DOWN = "down"
    PAUSED = "paused"
