import enum
import string
from dataclasses import dataclass


class Direction(enum.Enum):
    input = "input"
    output = "output"


class Color(enum.Enum):
    black = 0
    white = 3
    red = 5
    green = 17


class Scroll(str, enum.Enum):
    none = "none"
    left = "left"
    right = "right"


class ButtonState(str, enum.Enum):
    on = "on"
    off = "off"
    err = "err"
    no_change = "no_change"


@dataclass
class RGB:
    r: int = 0
    g: int = 0
    b: int = 0

    def scale(self, minimum, maximum) -> "RGB":
        """Scale the color range to [minimum, maximum]."""
        return RGB(
            r=int(((self.r / 255.0) * (maximum - minimum)) + minimum),
            g=int(((self.g / 255.0) * (maximum - minimum)) + minimum),
            b=int(((self.b / 255.0) * (maximum - minimum)) + minimum),
        )

    @property
    def hex(self):
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @staticmethod
    def __check_color_string(color: str) -> str:
        color = color.strip()
        if (
            len(color) == 7
            and color[0] == "#"
            and all([color[i] in string.hexdigits for i in range(1, 7)])
        ):
            return color[1:]
        elif len(color) == 6 and all(
            [color[i] in string.hexdigits for i in range(6)]
        ):
            return color
        else:
            raise ValueError(f"Invalid color string: {color}")

    @classmethod
    def parse(cls, color: str) -> "RGB":
        """Parse color string."""
        color = cls.__check_color_string(color=color)
        return cls(
            r=int(color[:2], 16), g=int(color[2:4], 16), b=int(color[4:], 16),
        )
