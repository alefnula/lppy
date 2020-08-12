import sys
import json
import inspect
import importlib
from pathlib import Path
from functools import partial
from typing import Optional, Callable
from dataclasses import dataclass

from lppy.midi import Message
from lppy.enums import RGB, ButtonState, Scroll
from lppy.models.launchpad import LaunchpadBase


@dataclass
class Result:
    char: Optional[str] = None
    text: Optional[str] = None
    color: RGB = RGB(r=255)
    scroll: Scroll = Scroll.none
    wait_ms: int = 1000


class Callback:
    def __init__(self, action: str, button: "Button"):
        self.action = action
        self.button = button
        self.callback = self.__get_callback(action)
        self.need_button = self.__need_button(self.callback)

    @staticmethod
    def __get_callback(action: str) -> Optional[Callable]:
        try:
            module_name, callback_name = action.split(":")
            module = importlib.import_module(module_name)
            return getattr(module, callback_name)
        except Exception as e:
            print("Error while importing callback:", e)
            return None

    @staticmethod
    def __need_button(callable) -> bool:
        sig = inspect.signature(callable)
        for parameter in sig.parameters.values():
            if parameter.annotation is Button:
                return True
        return False

    def __call__(self) -> Result:
        try:
            if self.need_button:
                return self.callback(self.button)
            else:
                return self.callback()
        except Exception as e:
            print("Error running callback:", e)
            return Result()


class Button:
    State = ButtonState

    def __init__(
        self,
        led_on: partial,
        n: int,
        action: str,
        color_on: RGB,
        color_off: RGB = RGB(),  # black / turned off
        color_err: RGB = RGB(r=255),  # red
        initial_state: ButtonState = ButtonState.off,
    ):
        """Create a button.

        Args:
            led_on: Function for turnging the led on.
            n: Button number.
            action: String path to the callback.
            color_on: Button on color.
            color_off: Button off color.
            color_err: Button error color.
            initial_state: Initial button state.
        """
        self.n = n
        self.action = action
        self.state = initial_state
        self.color_on = color_on
        self.color_off = color_off
        self.color_err = color_err
        self._led_on = led_on
        self.callback = Callback(action=action, button=self)

    @classmethod
    def from_dict(cls, led_on: partial, d: dict) -> "Button":
        button = cls(
            led_on=led_on,
            n=d["n"],
            action=d["action"],
            color_on=RGB.parse(d["color_on"]),
            color_off=RGB.parse(d["color_off"]),
        )
        if "color_err" in d:
            button.color_err = RGB.parse(d["color_err"])
        if "initial_state" in d:
            button.state = ButtonState(d["initial_state"])

        return button

    @property
    def on(self):
        return self.state == ButtonState.on

    @property
    def off(self):
        return self.state == ButtonState.off

    def led_on(self):
        if self.state == ButtonState.on:
            self._led_on(self.color_on)
        elif self.state == ButtonState.off:
            self._led_on(self.color_off)
        elif self.state == ButtonState.err:
            self._led_on(self.color_off)

    def led_off(self):
        self._led_on(RGB())

    def set_state(self, state: ButtonState):
        self.state = state
        self.led_on()

    def execute(self) -> Result:
        return self.callback()


class Layout:
    def __init__(self, path: str, launchpad: LaunchpadBase):
        """Initialize layout from json file.

        Args:
            path (str): Path to the layout json file.
            launchpad (LaunchpadBase): Instance of a launchpad.
        """
        self.path = Path(path)
        self.launchpad = launchpad

        data = json.loads(self.path.read_text(encoding="utf-8"))

        # Add script directory to python path
        python_path = str(self.path.parent.absolute())
        if python_path not in sys.path:
            sys.path.insert(0, python_path)

        # Load layout
        self.layout = {}
        for button_data in data["layout"]:
            n = button_data["n"]
            button = Button.from_dict(
                led_on=partial(self.launchpad.led_on, n=n), d=button_data,
            )
            self.layout[button.n] = button

        self.reset()

        self.launchpad.input.set_callback(self.callback)

    def reset(self, other_led_off=True):

        if other_led_off:
            # Reset all leds
            self.launchpad.led_all_off()

        # Put all buttons in the off state
        for button in self.layout.values():
            button.led_on()

    def callback(self, msg: Message):
        try:
            if msg.off:
                return

            button = self.layout.get(msg.n, None)
            if button is not None:
                result = button.execute()
                if result is None:
                    return

                if result.char is not None:
                    self.launchpad.write_char(
                        char=result.char, color=result.color
                    )
                    self.reset(other_led_off=False)
                elif result.text:
                    self.launchpad.write_string(
                        string=result.text,
                        color=result.color,
                        scroll=result.scroll,
                        wait_ms=result.wait_ms,
                    )
                    self.reset()
                else:
                    self.reset()

        except Exception as e:
            print(f"Failed to execute button: {msg.n}. Error: {e}")
