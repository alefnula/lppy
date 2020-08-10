import sys
import json
import inspect
import importlib
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from lppy.enums import RGB, ButtonState, Scroll
from lppy.models.launchpad import LaunchpadBase


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

    def __call__(self):
        try:
            if self.need_button:
                self.callback(self.button)
            else:
                self.callback()
        except Exception as e:
            print("Error running callback:", e)


class Button:
    State = ButtonState

    def __init__(
        self,
        lp: LaunchpadBase,
        n: int,
        action: str,
        color_on: RGB,
        color_off: RGB = RGB(),
        color_err: RGB = RGB(r=255),
    ):
        """Create a button.

        Args:
            lp: Instance of a launchpad used.
            n: Button number.
            action: String path to the callback.
            color_on: Button on color.
            color_off: Button off color.
            color_err: Button error color.
        """
        self.lp = lp
        self.n = n
        self.action = action
        self.state = ButtonState.off
        self.color_on = color_on
        self.color_off = color_off
        self.color_err = color_err
        self.callback = Callback(action=action, button=self)

    @classmethod
    def from_dict(cls, lp: LaunchpadBase, d: dict) -> "Button":
        button = cls(
            lp=lp,
            n=d["n"],
            action=d["action"],
            color_on=RGB.parse(d["color_on"]),
            color_off=RGB.parse(d["color_off"]),
        )
        if "color_err" in d:
            button.color_err = RGB.parse(d["color_err"])
        return button

    def turn_on(self):
        if self.state == ButtonState.on:
            self.lp.led_on(self.color_on, n=self.n)
        elif self.state == ButtonState.off:
            self.lp.led_on(self.color_off, n=self.n)
        elif self.state == ButtonState.err:
            self.lp.led_on(self.color_off, n=self.n)

    def turn_off(self):
        self.lp.led_on(RGB(), n=self.n)

    def set_state(self, state: ButtonState):
        self.state = state
        self.turn_on()

    def execute(self):
        self.callback()


@dataclass
class Result:
    state: ButtonState
    text: Optional[str] = None
    text_color: RGB = RGB(r=255)
    scroll: Scroll = Scroll.left

    @classmethod
    def from_dict(cls, d: dict) -> "Result":
        result = cls(state=ButtonState(d["state"]), text=d.get("text", None))
        if "text_color" in d:
            result.text_color = RGB.parse(d["text_color"])
        if "scroll" in d:
            result.scroll = Scroll(d["scroll"])
        return result


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
            button = Button.from_dict(lp=self.launchpad, d=button_data)
            self.layout[button.n] = button

        self.reset()

        self.launchpad.input.set_callback(self.callback)

    def reset(self):
        # Reset all leds
        self.launchpad.led_all_off()

        # Put all buttons in the off state
        for button in self.layout.values():
            button.turn_on()

    def callback(self, msg):
        try:
            if msg[0][0] == 144 and msg[0][2] == 127:
                button_no = msg[0][1]
                if button_no == 19:
                    self.reset()
                else:
                    button = self.layout.get(button_no, None)
                    if button is not None:
                        button.execute()
        except Exception as e:
            print(e)
