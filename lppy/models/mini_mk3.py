import enum
from typing import Optional

from lppy import errors
from lppy.enums import Color, RGB
from lppy.models.pro import LaunchpadPro


class LaunchpadMiniMk3(LaunchpadPro):
    """For 3-color "Mk3" Launchpads; Mini and Pro."""

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC)
    #
    #
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |104|   |106|   |   |   |   |111|  |112|
    #        +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 81|   |   |   |   |   |   |   |  | 89|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 71|   |   |   |   |   |   |   |  | 79|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 61|   |   |   |   |   | 67|   |  | 69|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 51|   |   |   |   |   |   |   |  | 59|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 41|   |   |   |   |   |   |   |  | 49|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 31|   |   |   |   |   |   |   |  | 39|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 21|   | 23|   |   |   |   |   |  | 29|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 11|   |   |   |   |   |   |   |  | 19|
    #        +---+---+---+---+---+---+---+---+  +---+
    #
    #
    #
    # LED AND BUTTON NUMBERS IN XY MODE (X/Y)
    #
    #          0   1   2   3   4   5   6   7      8
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |0/0|   |2/0|   |   |   |   |   |  |8/0|  0
    #        +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |0/1|   |   |   |   |   |   |   |  |   |  1
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  2
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |5/3|   |   |  |   |  3
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  4
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  5
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |4/6|   |   |   |  |   |  6
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  7
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |8/8|  8
    #        +---+---+---+---+---+---+---+---+  +---+
    #

    # 	COLORS = {'black':0, 'off':0, 'white':3, 'red':5, 'green':17 }

    INPUT_NAME = ("Launchpad Mini MK3", 1)
    OUTPUT_NAME = ("Launchpad Mini MK3", 1)

    class Layout(enum.Enum):
        session = 0x00
        drums = 0x04
        keys = 0x05
        user = 0x06
        daw = 0x0D
        programmer = 0x7F

    class Mode(enum.Enum):
        ableton_live_mode = 0
        programmer_mode = 1

    def open(self):
        super().open()
        self.set_mode(self.Mode.programmer_mode)
        self.set_layout(self.Layout.programmer)

    def close(self):
        """Close this Launchpad."""
        # We have to go back to custom modes before closing the connection,
        # otherwise Launchpad will stuck in programmer mode.
        if self.output is not None and self.output.is_open:
            self.set_layout(self.Layout.keys)
        super().close()

    def set_layout(self, layout: Layout = Layout.session):
        """Sets the button layout to the set, specified by the layout.

        Args:
            layout (Layout): Layout value.
        """
        self.output.send_sysex([0, 32, 41, 2, 13, 0, layout.value])

    def set_mode(self, mode: Mode = Mode.programmer_mode):
        """Selects the Mk3's mode."""
        self.output.send_sysex([0, 32, 41, 2, 13, 14, mode.value])

    def led_all_on(self, color: Color):
        """Quickly sets all all LEDs to the same color."""
        # TODO: Maybe the SysEx was indeed a better idea :)
        #       Did some tests:
        #         MacOS:   Doesn't matter.
        #         Windows: SysEx much better.
        #         Linux:   Completely freaks out.
        for x in range(9):
            for y in range(9):
                self.output.send(144, (x + 1) + ((y + 1) * 10), color.value)

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
                [0, 32, 41, 2, 13, 3, 3, n, color.r, color.g, color.b]
            )
        elif x is not None and y is not None:
            if x < 0 or x > 9 or y < 0 or y > 9:
                raise errors.LEDSelectionError(n=n, x=x, y=y)
            led = 90 - (10 * y) + x
            self.output.send_sysex(
                [0, 32, 41, 2, 13, 3, 3, led, color.r, color.g, color.b]
            )
        else:
            raise errors.LEDSelectionError(n=n, x=x, y=y)
