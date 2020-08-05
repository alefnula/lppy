import enum
from typing import Optional

from lppy.enums import Direction


class ErrorCode(enum.Enum):
    unknown = "unknown"
    value_error = "value error"
    device_not_found = "device not found"
    led_selection_error = "led selection error"


class LaunchpadError(Exception):
    Code = ErrorCode

    def __init__(self, message: str, code: Code = Code.unknown):
        self.message = message
        self.code = code

    @property
    def class_name(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.class_name}({self.code.name}: {self.message})"

    __repr__ = __str__


class DeviceNotFound(LaunchpadError):
    def __init__(self, name: str, direction: Direction):
        """DeviceNotFound error.

        Args:
            name (str): Name of the device.
            direction (Direction): Is it an input or output device.
        """
        self.name = name
        self.direction = direction

        if direction == Direction.input:
            message = f"Input device [{name}] not found."
        elif direction == Direction.output:
            message = f"Output device [{name}] not found."
        else:
            message = f"Device [{name}] not found."
        super().__init__(message=message, code=self.Code.device_not_found)


class InputDeviceNotFound(DeviceNotFound):
    def __init__(self, name: str):
        super().__init__(name=name, direction=Direction.input)


class OutputDeviceNotFound(DeviceNotFound):
    def __init__(self, name: str):
        super().__init__(name=name, direction=Direction.output)


class LEDSelectionError(LaunchpadError):
    def __init__(self, n: Optional[int], x: Optional[int], y: Optional[int]):
        self.n = n
        self.x = x
        self.y = y

        super().__init__(
            message=f"Invalid LED selection: n={n}, x={x}, y={y}",
            code=ErrorCode.led_selection_error,
        )
