import enum
import queue
import logging
import threading
from typing import Union, Optional, Tuple

import rtmidi

from lppy import errors
from lppy.enums import Direction

logger = logging.getLogger(__name__)


class Message:
    class State(str, enum.Enum):
        off = "off"
        on = "on"

    def __init__(self, n: int, intensity: int = 0, diff: float = 0.0):
        # FIXME: Only for MK3
        self.state = self.State.on if intensity == 127 else self.State.off
        self.n = n
        self.intensity = intensity
        self.diff = diff

    def __str__(self):
        return f"Message(state={self.state}, n={self.n})"

    __repr__ = __str__

    @property
    def on(self):
        return self.state == self.State.on

    @property
    def off(self):
        return self.state == self.State.off


class Device:
    def __init__(self, midi: Union[rtmidi.MidiIn, rtmidi.MidiOut]):
        self.midi = midi

    @property
    def is_open(self):
        return self.midi is not None

    def close(self):
        self.midi.delete()
        del self.midi
        self.midi = None


class InputDevice(Device):
    def __init__(self, midi: rtmidi.MidiIn):
        super().__init__(midi=midi)
        self.__message_queue = queue.Queue()
        self.__callback_queue = queue.Queue()
        self.__callbacks = []
        self.midi.set_callback(self.__callback)
        self.__stop_event = threading.Event()
        self.__thread = threading.Thread(
            target=self.__handle_callbacks, daemon=True
        )
        self.__thread.start()

    def __callback(self, message, data=None):
        ((code, n, intensity), diff) = message
        # FIXME: This is only for MK3 need info about other Launchpads
        if code in (144, 176):
            msg = Message(n=n, intensity=intensity, diff=diff)
            self.__message_queue.put_nowait(msg)
            self.__callback_queue.put_nowait(msg)

    def __handle_callbacks(self):
        while not self.__stop_event.is_set():
            try:
                message = self.__callback_queue.get()
                for callback in self.__callbacks:
                    callback(message)
            except Exception:
                # FIXME: What can be raised?
                pass

    def close(self):
        self.__stop_event.set()
        super().close()

    def read(self):
        """Get a single message."""
        try:
            return self.__message_queue.get_nowait()
        except queue.Empty:
            return None

    def flush(self):
        """Remove all messages from the queue."""
        with self.__message_queue.mutex:
            self.__message_queue.queue.clear()
        with self.__callback_queue.mutex:
            self.__callback_queue.queue.clear()

    def set_callback(self, callback):
        if callback not in self.__callbacks:
            self.__callbacks.append(callback)

    def remove_callback(self, callback):
        if callback in self.__callbacks:
            self.__callbacks.remove(callback)


class OutputDevice(Device):
    def __init__(self, midi: rtmidi.MidiOut):
        super().__init__(midi=midi)

    def send(self, stat, dat1, dat2):
        """Send a single message."""
        self.midi.send_message([stat, dat1, dat2])

    def send_sysex(self, messages):
        """Send a single system-exclusive message, given by list messages.

        The start (0xF0) and end bytes (0xF7) are added automatically.

        Message should be in a format::

            [ <dat1>, <dat2>, ..., <datN> ]

        """
        self.midi.send_message([0xF0] + messages + [0xF7])


class Midi:
    Direction = Direction

    @staticmethod
    def search_for_device(name: Optional[str], direction: Direction) -> bool:
        """Search for a device by name and direction.

        The device won't be opened.

        Args:
            name (str, optional): Partial match of the device name. If it's set
                to ``None`` the return value will be ``None``.
            direction (Direction): Is it an input or output device.

        Returns:
            bool: ``True`` if the device is found ``False`` otherwise.
        """
        if direction == Direction.input:
            midi = rtmidi.MidiIn()
        elif direction == Direction.output:
            midi = rtmidi.MidiOut()
        else:
            raise errors.LaunchpadError(
                message=f"Invalid direction value: {direction}",
                code=errors.ErrorCode.value_error,
            )

        for i, port in enumerate(midi.get_ports()):
            if port.lower().find(name.lower()) != -1:
                midi.delete()
                del midi
                return True

        midi.delete()
        del midi
        return False

    @staticmethod
    def open_device(
        name: Optional[Tuple[str, int]], direction: Direction
    ) -> Optional[Union[InputDevice, OutputDevice]]:
        """Open an input device by it's partial name match.

        Args:
            name (str, optional): Partial match of the device name. If it's set
                to ``None`` the return value will be ``None``.
            direction (Direction): Is it an input or output device.

        Returns:
            Optional[Union[rtmidi.MidiIn, rtmidi.MidiOut]]: Instance of a
                ``MidiIn`` or ``MidiOut`` class if appropriate device is found
                or ``None`` if the device is not found or the name is not
                provided.
        """
        if name is None:
            return None

        if direction == Direction.input:
            midi = rtmidi.MidiIn()
            error_class = errors.InputDeviceNotFound
            wrapper_class = InputDevice
        elif direction == Direction.output:
            midi = rtmidi.MidiOut()
            error_class = errors.OutputDeviceNotFound
            wrapper_class = OutputDevice
        else:
            raise errors.LaunchpadError(
                message=f"Invalid direction value: {direction}",
                code=errors.ErrorCode.value_error,
            )

        # FIXME: Hack!
        name, no = name
        found = -1
        for i, port in enumerate(midi.get_ports()):
            if port.lower().find(name.lower()) != -1:
                found += 1
                if found == no:
                    midi.open_port(i)
                    return wrapper_class(midi)

        midi.delete()
        del midi
        raise error_class(name)
