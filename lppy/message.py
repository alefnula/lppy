import enum
from dataclasses import dataclass


class Action(enum.Enum):
    press = "press"
    release = "release"
    click = "click"


@dataclass
class Message:
    Action = Action

    action: Action
    code: int
    n: int
    intensity: int = 0
    diff: float = 0.0

    @property
    def duration(self):
        if self.action == self.Action.click:
            return self.diff
        return 0
