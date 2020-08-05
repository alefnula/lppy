import enum
from dataclasses import dataclass


class Direction(enum.Enum):
    input = "input"
    output = "output"


class Color(enum.Enum):
    black = 0
    white = 3
    red = 5
    green = 17


class Scroll(enum.Enum):
    none = 0
    left = -1
    right = 1


@dataclass
class RGB:
    red: int = 0
    green: int = 0
    blue: int = 0

    def scale(self, minimum, maximum) -> "RGB":
        """Scale the color range to [minimum, maximum]."""
        return RGB(
            red=int(((self.red / 255.0) * (maximum - minimum)) + minimum),
            green=int(((self.green / 255.0) * (maximum - minimum)) + minimum),
            blue=int(((self.blue / 255.0) * (maximum - minimum)) + minimum),
        )
