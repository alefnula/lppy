import enum
from typing import Optional

from lppy import errors
from lppy.chartab import CHAR_TAB
from lppy.enums import Color, RGB
from lppy.models.launchpad import LaunchpadBase


class LaunchpadPro(LaunchpadBase):
    """For 3-color "Pro" Launchpads with 8x8 matrix.

    And 4x8 left/right/top/bottom rows
    """

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC)
    # WITH LAUNCHPAD IN "LIVE MODE" (PRESS SETUP, top-left GREEN).
    #
    # Notice that the fine manual doesn't know that mode.
    # According to what's written there, the numbering used
    # refers to the "PROGRAMMING MODE", which actually does
    # not react to any of those notes (or numbers).
    #
    #        +---+---+---+---+---+---+---+---+
    #        | 91|   |   |   |   |   |   | 98|
    #        +---+---+---+---+---+---+---+---+
    #
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 80|  | 81|   |   |   |   |   |   |   |  | 89|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 70|  |   |   |   |   |   |   |   |   |  | 79|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 60|  |   |   |   |   |   |   | 67|   |  | 69|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 50|  |   |   |   |   |   |   |   |   |  | 59|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 40|  |   |   |   |   |   |   |   |   |  | 49|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 30|  |   |   |   |   |   |   |   |   |  | 39|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 20|  |   |   | 23|   |   |   |   |   |  | 29|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 10|  |   |   |   |   |   |   |   |   |  | 19|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+
    #        |  1|  2|   |   |   |   |   |  8|
    #        +---+---+---+---+---+---+---+---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY CLASSIC MODE (X/Y)
    #
    #   9      0   1   2   3   4   5   6   7      8
    #        +---+---+---+---+---+---+---+---+
    #        |0/0|   |2/0|   |   |   |   |   |         0
    #        +---+---+---+---+---+---+---+---+
    #
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |0/1|   |   |   |   |   |   |   |  |   |  1
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |9/2|  |   |   |   |   |   |   |   |   |  |   |  2
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |5/3|   |   |  |   |  3
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  4
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  5
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |4/6|   |   |   |  |   |  6
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  7
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |9/8|  |   |   |   |   |   |   |   |   |  |8/8|  8
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+
    #        |   |1/9|   |   |   |   |   |   |         9
    #        +---+---+---+---+---+---+---+---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY PRO MODE (X/Y)
    #
    #   0      1   2   3   4   5   6   7   8      9
    #        +---+---+---+---+---+---+---+---+
    #        |1/0|   |3/0|   |   |   |   |   |         0
    #        +---+---+---+---+---+---+---+---+
    #
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |1/1|   |   |   |   |   |   |   |  |   |  1
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |0/2|  |   |   |   |   |   |   |   |   |  |   |  2
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |6/3|   |   |  |   |  3
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  4
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  5
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |5/6|   |   |   |  |   |  6
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  7
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |0/8|  |   |   |   |   |   |   |   |   |  |9/8|  8
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+
    #        |   |2/9|   |   |   |   |   |   |         9
    #        +---+---+---+---+---+---+---+---+
    #
    INPUT_NAME = ("Pro", 0)
    OUTPUT_NAME = ("Pro", 0)

    class Layout(enum.Enum):
        session = 0x00
        drum_rack = 0x01
        chromatic_note = 0x02
        user = 0x03
        audio = 0x04
        fader = 0x05
        record_arm = 0x06
        track_select = 0x07
        mute = 0x08
        solo = 0x09
        volume = 0x0A

    class Mode(enum.Enum):
        ableton_live_mode = 0
        standalone_mode = 1

    def set_layout(self, layout: Layout = Layout.session):
        """Sets the button layout to the set, specified by the layout.

        Args:
            layout (Layout): Layout value.
        """
        self.output.send_sysex([0, 32, 41, 2, 16, 34, layout.value])

    def set_mode(self, mode: Mode = Mode.ableton_live_mode):
        """Selects the Pro's mode."""
        self.output.send_sysex([0, 32, 41, 2, 16, 33, mode.value])

    def led_all_on(self, color: Color):
        """Quickly sets all all LEDs to the same color."""
        self.output.send_sysex([0, 32, 41, 2, 16, 14, color.value])

    def led_on(
        self,
        color: RGB,
        n: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):

        # Red green and blue can be only between 0-63
        color = color.scale(minimum=0, maximum=63)

        if n is not None:
            if n < 0 or n > 99:
                raise errors.LEDSelectionError(n=n, x=x, y=y)

            self.output.send_sysex(
                [0, 32, 41, 2, 16, 11, n, color.r, color.g, color.b]
            )
        elif x is not None and y is not None:
            if x < 0 or x > 9 or y < 0 or y > 9:
                raise errors.LEDSelectionError(n=n, x=x, y=y)
            led = 90 - (10 * y) + x
            self.output.send_sysex(
                [0, 32, 41, 2, 16, 11, led, color.r, color.g, color.b]
            )
        else:
            raise errors.LEDSelectionError(n=n, x=x, y=y)

    def write_char(self, char: str, color: RGB, offset: int = 0):
        """Write character in colors and lateral offset."""
        codes = CHAR_TAB[self._limit(ord(char), minimum=0, maximum=255)]
        index = 0
        black = RGB()

        for i in range(81, 1, -10):
            for j in range(8):
                n = i + j + offset
                if i <= n < i + 8:
                    if codes[index] & 0x80 >> j:
                        self.led_on(color, n=n)
                    else:
                        self.led_on(black, n=n)
            index += 1
