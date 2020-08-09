import time
from typing import Optional

from lppy.enums import Color, RGB, Scroll
from lppy.midi import Midi, InputDevice, OutputDevice


class LaunchpadBase:
    INPUT_NAME: Optional[str] = None
    OUTPUT_NAME: Optional[str] = None

    Color = Color
    RGB = RGB
    Scroll = Scroll

    def __init__(self):
        self.input: Optional[InputDevice] = None
        self.output: Optional[OutputDevice] = None
        self.open()

    def __delete__(self):
        self.close()

    def open(self):
        """Open launchpad devices."""
        # First close them if they are already open
        self.close()
        self.input = Midi.open_device(
            name=self.INPUT_NAME, direction=Midi.Direction.input
        )
        self.output = Midi.open_device(
            name=self.OUTPUT_NAME, direction=Midi.Direction.output
        )

    def close(self):
        """Close this Launchpad."""
        if self.input is not None and self.input.is_open:
            self.input.close()
            self.input = None
        if self.output is not None and self.output.is_open:
            self.output.close()
            self.output = None

    def flush_buttons(self):
        """Clear the button buffer.

        The Launchpads remember everything.

        Because of empty reads (timeouts), there's nothing more we can do here,
        but repeat the polls and wait a little...
        """
        self.input.flush()

    def reset(self):
        """Reset the Launchpad.

        Turns off all LEDs.
        """
        self.led_all_on(color=Color.black)

    def led_all_on(self, color: Color = Color.black):
        """All LEDs on.

        Args:
            color (Color): Turn LEDs on and set the color. Color.black means
                turn LEDs off.
        """
        raise NotImplementedError()

    def led_on(
        self,
        color: RGB,
        n: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):
        """Turn on the selected LED using selected color.

        Led can be selected either by passing in the led number ``n`` or
        by selecting the ``x`` and ``y`` position of the led.

        Args:
            color (RGB): Selected RGB color.
            n (int, optional): LED's number.
            x (int, optional): x coordinate of the LED.
            y (int, optional): y coordinate of the LED.
        """
        raise NotImplementedError()

    def write_char(self, char: str, color: RGB, offset: int = 0):
        """Write character in colors and lateral offset."""
        raise NotImplementedError()

    def write_string(
        self,
        string: str,
        color: RGB,
        scroll: Scroll = Scroll.none,
        wait_ms=100,
    ):
        """Scroll string with color."""
        if scroll == Scroll.left:
            string += " "  # just to avoid artifacts on full width characters
            for n in range((len(string) + 1) * 8):
                if n <= len(string) * 8:
                    self.write_char(
                        string[self._limit((n // 16) * 2, 0, len(string) - 1)],
                        color,
                        8 - n % 16,
                    )
                if n > 7:
                    self.write_char(
                        string[
                            self._limit(
                                (((n - 8) // 16) * 2) + 1, 0, len(string) - 1
                            )
                        ],
                        color,
                        8 - (n - 8) % 16,
                    )
                time.sleep(0.001 * wait_ms)

        elif scroll == Scroll.right:
            # TODO: Just a quick hack (screen is erased before scrolling
            #       begins). Characters at odd positions from the right
            #       (1, 3, 5), with pixels at the left, e.g. 'C' will have
            #       artifacts at the left (pixel repeated).

            # just to avoid artifacts on full width characters
            string = " " + string + " "
            # for n in range( (len(string) + 1) * 8 - 1, 0, -1 ):
            for n in range((len(string) + 1) * 8 - 7, 0, -1):
                if n <= len(string) * 8:
                    self.write_char(
                        string[self._limit((n // 16) * 2, 0, len(string) - 1)],
                        color,
                        8 - n % 16,
                    )
                if n > 7:
                    self.write_char(
                        string[
                            self._limit(
                                (((n - 8) // 16) * 2) + 1, 0, len(string) - 1
                            )
                        ],
                        color,
                        8 - (n - 8) % 16,
                    )
                time.sleep(0.001 * wait_ms)
        else:
            # TODO: not a good idea :)
            for i in string:
                for n in range(4):
                    # pseudo repetitions to compensate the timing a bit
                    self.write_char(i, color)
                    time.sleep(0.001 * wait_ms)

    @staticmethod
    def _limit(n: int, minimum: int, maximum: int):
        """Limit n between minimum and maximum."""
        return max(min(maximum, n), minimum)
