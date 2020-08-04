import time

from lppy.midi import Midi
from lppy.chartab import CHAR_TAB


class LaunchpadBase:
    def __init__(self):
        self.midi = Midi()  # midi interface instance (singleton)
        self.output_id = None  # midi id for output
        self.input_id = None  # midi id for input
        self.msg = None  # callback message

        # scroll directions
        self.SCROLL_NONE = 0
        self.SCROLL_LEFT = -1
        self.SCROLL_RIGHT = 1

    def __delete__(self):
        self.close()

    def open(self, n=0, name="Launchpad") -> bool:
        """Open one of the attached Launchpad MIDI devices."""
        self.output_id = self.midi.search_device(
            name, output=True, input=False, n=n
        )
        self.input_id = self.midi.search_device(
            name, output=False, input=True, n=n
        )

        if self.output_id is None or self.input_id is None:
            return False

        if not self.midi.output_open(self.output_id):
            return False

        return self.midi.input_open(self.input_id)

    def check(self, n=0, name="Launchpad") -> bool:
        """Check if a device exists, but does not open it.

        Does not check whether a device is in use or other, strange things.
        """
        self.output_id = self.midi.search_device(
            name, output=True, input=False, n=n
        )
        self.input_id = self.midi.search_device(
            name, output=False, input=True, n=n
        )

        if self.output_id is None or self.input_id is None:
            return False

        return True

    def close(self):
        """Close this device."""
        self.midi.input_close()
        self.midi.output_close()

    def list_all(self, quiet=True):
        """Return a list of all devices."""
        return self.midi.search_devices(
            "*", output=True, input=True, quiet=quiet
        )

    def button_flush(self):
        """Clear the button buffer (The Launchpads remember everything...).

        Because of empty reads (timeouts), there's nothing more we can do here,
        but repeat the polls and wait a little...
        """
        n_reads = 0
        # wait for that amount of consecutive read fails to exit
        while n_reads < 3:
            a = self.midi.read_raw()
            if a:
                n_reads = 0
            else:
                n_reads += 1
                time.sleep(0.001 * 5)

    def events_raw(self):
        """Return a list of all MIDI events, empty list if nothing happened.

        Useful for debugging or checking new devices.
        """
        msg = self.midi.read_raw()
        return msg if msg else []


class Launchpad(LaunchpadBase):
    """For 2-color Launchpads with 8x8 matrix and 2x8 top/right rows."""

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC):
    #
    # +---+---+---+---+---+---+---+---+
    # |200|201|202|203|204|205|206|207| < AUTOMAP BUTTON CODES;
    # +---+---+---+---+---+---+---+---+   Or use LedCtrlAutomap() for LEDs.
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

    def reset(self):
        """Reset the Launchpad.

        Turns off all LEDs.
        """
        self.midi.write_raw(176, 0, 0)

    @staticmethod
    def led_get_color(red, green):
        """Returns a Launchpad compatible "color code byte".

        NOTE: In here, number is 0..7 (left..right).
        """
        led = 0

        red = min(int(red), 3)  # make int and limit to <=3
        red = max(red, 0)  # no negative numbers

        green = min(int(green), 3)  # make int and limit to <=3
        green = max(green, 0)  # no negative numbers

        led |= red
        led |= green << 4

        return led

    def led_control_raw(self, number, red, green):
        """Control a grid LED.

         By its raw <number>; with <green/red> brightness: 0..3

        For LED numbers, see grid description on top of class.
        """
        if number > 199:
            if number < 208:
                # 200-207
                self.led_control_automap(number - 200, red, green)
        else:
            if number < 0 or number > 120:
                return
            # 0-120
            led = self.led_get_color(red, green)
            self.midi.write_raw(144, number, led)

    def led_control_xy(self, x, y, red, green):
        """Control a grid LED by its coordinates.

        <x> and <y>  with <green/red> brightness 0..3
        """
        if x < 0 or x > 8 or y < 0 or y > 8:
            return

        if y == 0:
            self.led_control_automap(x, red, green)

        else:
            self.led_control_raw(((y - 1) << 4) | x, red, green)

    def led_control_raw_rapid(self, all_leds):
        """Sends a list of consecutive, special color values to the Launchpad.

        Only requires (less than) half of the commands to update all buttons.

        [ LED1, LED2, LED3, ... LED80 ]

        First, the 8x8 matrix is updated, left to right, top to bottom.

        Afterwards, the algorithm continues with the rightmost buttons and the
        top "automap" buttons.

        LEDn color format: 00gg00rr <- 2 bits green, 2 bits red (0..3)

        Function led_get_color() will do the coding for you.

        Notice that the amount of LEDs needs to be even.

        If an odd number of values is sent, the next, following LED is turned
        off!
        """
        le = len(all_leds)

        for i in range(0, le, 2):
            self.midi.write_raw(
                146, all_leds[i], all_leds[i + 1] if i + 1 < le else 0
            )

    #   This fast version does not work, because the Launchpad gets confused
    #   by the timestamps...
    #
    # 		tmsg= []
    # 		for i in range( 0, le, 2 ):
    # 			# create a message
    # 			msg = [ 146 ]
    # 			msg.append( allLeds[i] )
    # 			if i+1 < le:
    # 				msg.append( allLeds[i+1] )
    # 			# add it to the list
    # 			tmsg.append( msg )
    # 			# add a timestanp
    # 			tmsg.append( self.midi.GetTime() + i*10 )
    #
    # 		self.midi.RawWriteMulti( [ tmsg ] )

    def led_control_raw_rapid_home(self):
        """Home the next led_control_raw_rapid() call.

        So it will start with the first LED again.
        """
        self.midi.write_raw(176, 1, 0)

    def led_control_automap(self, number, red, green):
        """Control an automap LED <number>; with <green/red> brightness: 0..3.

        NOTE: In here, number is 0..7 (left..right).
        """
        if number < 0 or number > 7:
            return

        # TODO: limit red/green
        led = self.led_get_color(red, green)

        self.midi.write_raw(176, 104 + number, led)

    def led_all_on(self, color_code=None):
        """All LEDs on.

        <color_code> is here for backwards compatibility with the newer "Mk2"
        and "Pro".

        classes. If it's "0", all LEDs are turned off. In all other cases
        turned on, like the function name implies :-/.
        """
        if color_code == 0:
            self.reset()
        else:
            self.midi.write_raw(176, 0, 127)

    # -------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------
    def led_control_char(self, char, red, green, offset_x=0, offset_y=0):
        """Sends character <char> to the Launchpad.

        In colors <red/green> and lateral offset <offset_x> (-8..8)

        <offset_y> does not have yet any function.
        """
        char = ord(char)

        if char < 0 or char > 255:
            return

        codes = CHAR_TAB[char]

        index = 0

        for i in range(0, 8 * 16, 16):
            for j in range(8):
                led_num = i + j + offset_x
                if i <= led_num < i + 8:
                    if codes[index] & 0x80 >> j:
                        self.led_control_raw(led_num, red, green)
                    else:
                        self.led_control_raw(led_num, 0, 0)
            index += 1

    def led_control_string(
        self, string, red, green, direction=None, wait_ms=150
    ):
        """Scroll <string>, in colors specified by <red/green>.

        As fast as we can.

        <direction> specifies: -1 to left, 0 no scroll, 1 to right

        The delays were a dirty hack, but there's little to nothing one can do
        here.

        So that's how the <waitms> parameter came into play...
        """

        def limit(n, mini, maxi):
            return max(min(maxi, n), mini)

        if direction == self.SCROLL_LEFT:
            string += " "
            for n in range((len(string) + 1) * 8):
                if n <= len(string) * 8:
                    self.led_control_char(
                        string[limit((n // 16) * 2, 0, len(string) - 1)],
                        red,
                        green,
                        8 - n % 16,
                    )
                if n > 7:
                    self.led_control_char(
                        string[
                            limit(
                                (((n - 8) // 16) * 2) + 1, 0, len(string) - 1
                            )
                        ],
                        red,
                        green,
                        8 - (n - 8) % 16,
                    )
                time.sleep(0.001 * wait_ms)
        elif direction == self.SCROLL_RIGHT:
            # TODO: Just a quick hack (screen is erased before scrolling
            #       begins).
            #       Characters at odd positions from the right (1, 3, 5), with
            #       pixels at the left, e.g. 'C' will have artifacts at the
            #       left (pixel repeated).

            # just to avoid artifacts on full width characters
            string = " " + string + " "

            # for n in range( (len(string) + 1) * 8 - 1, 0, -1 ):
            for n in range((len(string) + 1) * 8 - 7, 0, -1):
                if n <= len(string) * 8:
                    self.led_control_char(
                        string[limit((n // 16) * 2, 0, len(string) - 1)],
                        red,
                        green,
                        8 - n % 16,
                    )
                if n > 7:
                    self.led_control_char(
                        string[
                            limit(
                                (((n - 8) // 16) * 2) + 1, 0, len(string) - 1
                            )
                        ],
                        red,
                        green,
                        8 - (n - 8) % 16,
                    )
                time.sleep(0.001 * wait_ms)
        else:
            # TODO: ah, uh, oh, wat?
            for i in string:
                for n in range(4):
                    # pseudo repetitions to compensate the timing a bit
                    self.led_control_char(i, red, green)
                    time.sleep(0.001 * wait_ms)

    def button_state_raw(self):
        """Returns the raw value of the last button change as a list.

        [ <button>, <True/False> ]
        """
        if self.msg:
            return [
                self.msg[1] if self.msg[0] == 144 else self.msg[1] + 96,
                True if self.msg[2] > 0 else False,
            ]
        else:
            return []

    def button_state_xy(self):
        """Returns an x/y value of the last button change as a list.

        [ <x>, <y>, <True/False> ]
        """
        if self.msg:

            if self.msg[0] == 144:
                x = self.msg[1] & 0x0F
                y = (self.msg[1] & 0xF0) >> 4

                return [x, y + 1, True if self.msg[2] > 0 else False]

            elif self.msg[0] == 176:
                return [
                    self.msg[1] - 104,
                    0,
                    True if self.msg[2] > 0 else False,
                ]

        return []
