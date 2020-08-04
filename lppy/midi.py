import logging
from typing import List, Optional

import rtmidi


logger = logging.getLogger(__name__)


class _Midi:
    def __init__(self):
        # exception handling moved to Midi()
        # midi.init()
        # but I can't remember why I put this one in here...
        # midi.get_count()
        pass

    def __del__(self):
        # This will never be executed, because no one knows, how many Launchpad
        # instances exist(ed) until we start to count them...
        #
        # midi.quit()
        pass

    @staticmethod
    def search_devices(
        name: str, output: bool = True, input: bool = True, quiet: bool = True
    ) -> List[int]:
        """Return a list of devices that match arguments.

        Args:
            name (str): Match by device name.
            output (bool): Has outputs?
            input (bool): Has inputs?
            quiet (bool): Don't print any debugging messages.

        Returns:
            List[int]: List of device numbers.
        """
        result: List[int] = []
        i = 0

        if output:
            midi_out = rtmidi.MidiOut()
            for port in midi_out.get_ports():
                if not quiet:
                    logger.info("Found output device: port=%s, 1, 0", port)
                if port.lower().find(name.lower()) >= 0:
                    result.append(i)
                i += 1

        if input:
            midi_in = rtmidi.MidiIn()
            for port in midi_in.get_ports():
                if not quiet:
                    logger.info("Found input device: port=%s, 1, 0", port)
                if port.lower().find(name.lower()) >= 0:
                    result.append(i)
                i += 1

        return result

    def search_device(
        self, name: str, output: bool = True, input: bool = True, n: int = 0
    ) -> Optional[int]:
        """Return the nth (default first) device that matches arguments.

        By default it will return the first (n=0) device.

        Args:
            name (str): Match by device name.
            output (bool): Has outputs?
            input (bool): Has inputs?
            n (int): Return nth device.

        Returns:
            Optional[int]: nth device (default first) if found else None.
        """
        result = self.search_devices(name, output, input)

        if not 0 <= n < len(result):
            return None

        return result[n]


class Midi:
    """Midi singleton wrapper."""

    __instance = None

    def __init__(self):
        """Allow only one instance to be created."""
        if Midi.__instance is None:
            try:
                Midi.__instance = _Midi()
            except Exception as e:
                logger.error("Failed to initialize MIDI. Error: %s", e)
                Midi.__instance = None

        self.device_in = None
        self.device_out = None

    def __getattr__(self, name):
        """Pass all unknown method calls to the instance of _Midi class."""
        return getattr(self.__instance, name)

    def output_open(self, midi_id: int) -> bool:
        """Try to open an output device.

        Args:
            midi_id (int): ID of the midi device.

        Returns:
            bool: True if succeeded False otherwise.
        """
        if self.device_out is None:
            try:
                self.device_out = rtmidi.MidiOut()
                self.device_out.open_port(midi_id)
            except Exception as e:
                logger.error(
                    "Failed to open an output device: %s. Error: %s",
                    midi_id,
                    e,
                )
                self.device_out = None
                return False
        return True

    def output_close(self):
        if self.device_out is not None:
            # self.devOut.close()
            del self.device_out
            self.device_out = None

    def input_open(
        self, midi_id: int, buffer_size: Optional[int] = None
    ) -> bool:
        """Try to open an output device.

        Args:
            midi_id (int): ID of the midi device.
            buffer_size (int, optional): Size of the buffer.

        Returns:
            bool: True if succeeded False otherwise.
        """
        if self.device_in is None:
            try:
                # rtmidi's default size of the buffer is 1024.
                self.device_in = (
                    rtmidi.MidiIn()
                    if buffer_size is None
                    else rtmidi.MidiIn(queue_size_limit=buffer_size)
                )
                self.device_in.open_port(midi_id)
            except Exception as e:
                logger.error(
                    "Failed to open an input device: %s. Error: %s",
                    midi_id,
                    e,
                )
                self.device_in = None
                return False
        return True

    def input_close(self):
        if self.device_in is not None:
            self.device_in.close_port()
            del self.device_in
            self.device_in = None

    def read_raw(self):
        msg = self.device_in.get_message()
        if msg != (None, None):
            return msg
        else:
            return None

    def write_raw(self, stat, dat1, dat2):
        """Send a single, short message."""
        self.device_out.send_message([stat, dat1, dat2])

    def write_raw_multi(self, messages):
        """Send a list of messages.

        If timestamp is 0, it is ignored.
        Amount of <dat> bytes is arbitrary.

        Messages should be in the following format::

            [
                [
                    [stat, <dat1>, <dat2>, <dat3>],
                    timestamp
                ],
                [...],
                ...
            ]

        <datN> fields are optional.

        Args:
            messages (list): List of messages.
        """
        self.device_out.send_message(messages)

    def write_raw_sysex(self, messages, timestamp=0):
        """Send a single system-exclusive message, given by list messages.

        The start (0xF0) and end bytes (0xF7) are added automatically.

        Message should be in a format::

            [ <dat1>, <dat2>, ..., <datN> ]

        Timestamp is not supported and will be sent as '0' (for now)
        """
        self.device_out.send_message([0xF0] + messages + [0xF7])
