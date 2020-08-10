from typing import Optional


from lppy import errors
from lppy.enums import Color, RGB
from lppy.chartab import CHAR_TAB
from lppy.base import LaunchpadBase


class Launchpad(LaunchpadBase):
    """For 2-color Launchpads with 8x8 matrix and 2x8 top/right rows."""

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC):
    #
    # +---+---+---+---+---+---+---+---+
    # |200|201|202|203|204|205|206|207|
    # +---+---+---+---+---+---+---+---+
    #
    # +---+---+---+---+---+---+---+---+  +---+
    # |  0|...|   |   |   |   |   |  7|  |  8|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 16|...|   |   |   |   |   | 23|  | 24|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 32|...|   |   |   |   |   | 39|  | 40|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 48|...|   |   |   |   |   | 55|  | 56|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 64|...|   |   |   |   |   | 71|  | 72|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 80|...|   |   |   |   |   | 87|  | 88|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 96|...|   |   |   |   |   |103|  |104|
    # +---+---+---+---+---+---+---+---+  +---+
    # |112|...|   |   |   |   |   |119|  |120|
    # +---+---+---+---+---+---+---+---+  +---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY MODE (X/Y)
    #
    #   0   1   2   3   4   5   6   7      8
    # +---+---+---+---+---+---+---+---+
    # |   |1/0|   |   |   |   |   |   |         0
    # +---+---+---+---+---+---+---+---+
    #
    # +---+---+---+---+---+---+---+---+  +---+
    # |0/1|   |   |   |   |   |   |   |  |   |  1
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  2
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |5/3|   |   |  |   |  3
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  4
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  5
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |4/6|   |   |   |  |   |  6
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  7
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |8/8|  8
    # +---+---+---+---+---+---+---+---+  +---+
    #

    INPUT_NAME = ("Launchpad", 0)
    OUTPUT_NAME = ("Launchpad", 0)

    def led_all_on(self, color: Color):
        """All LEDs on.

        Args:
            color (Color): This is here for compatibility with the newer
            "Mk2", "Pro", etc...classes. If it's ``Color.black``, all LEDs are
            turned off. In all other cases turned on, like the function name
            implies.
        """
        if color == Color.black:
            # Send reset message
            self.output.send(176, 0, 0)
        else:
            self.output.send(176, 0, 127)

    @staticmethod
    def _get_color(color: RGB) -> int:
        """Returns a Launchpad compatible "color code byte".

        NOTE: In here, number is 0..7 (left..right).
        """
        red = min(color.r, 3)  # make int and limit to <=3
        red = max(red, 0)  # no negative numbers

        green = min(int(color.g), 3)  # make int and limit to <=3
        green = max(green, 0)  # no negative numbers

        led = 0
        led |= red
        led |= green << 4
        return led

    def led_on(
        self,
        color: RGB,
        n: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):
        """Turn on the selected LED using selected color.

        LED's can use only green/red brightness: 0..3

        For LED numbers, see grid description on the top of class.
        """
        color = self._get_color(color)
        if n is not None:

            if 199 < n < 208:
                self.output.send(176, n - 200 + 104, color)
            elif n < 0 or n > 120:
                raise errors.LEDSelectionError(n=n, x=x, y=y)
            else:
                self.output.send(144, n, color)
        elif x is not None and y is not None:
            if x < 0 or x > 8 or y < 0 or y > 8:
                raise errors.LEDSelectionError(n=n, x=x, y=y)

            if y == 0:
                self.output.send(176, x + 104, color)
            else:
                self.output.send(144, ((y - 1) << 4) | x, color)
        else:
            raise errors.LEDSelectionError(n=n, x=x, y=y)

    def write_char(self, char: str, color: RGB, offset: int = 0):
        """Write character in colors and lateral offset."""
        codes = CHAR_TAB[self._limit(ord(char), minimum=0, maximum=255)]
        index = 0
        black = RGB()

        for i in range(0, 8 * 16, 16):
            for j in range(8):
                n = i + j + offset
                if i <= n < i + 8:
                    if codes[index] & 0x80 >> j:
                        self.led_on(color, n=n)
                    else:
                        self.led_on(black, n=n)
            index += 1
