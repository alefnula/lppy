import sys
import json
import inspect
import logging
import importlib
from pathlib import Path
from functools import partial
from typing import Optional, Callable
from dataclasses import dataclass

from lppy.midi import Message
from lppy.enums import RGB, ButtonState, Scroll
from lppy.models.launchpad import LaunchpadBase


logger = logging.getLogger(__name__)


def get_callable(path: str) -> Optional[Callable]:
    try:
        module_name, callable_name = path.split(":")
        module = importlib.import_module(module_name)
        return getattr(module, callable_name)
    except Exception as e:
        logger.error("Error while importing callable: %s", e)
        return None


@dataclass
class Result:
    char: Optional[str] = None
    text: Optional[str] = None
    color: RGB = RGB(r=255)
    scroll: Scroll = Scroll.none
    wait_ms: int = 1000


class Callback:
    def __init__(self, command: str, button: "Button"):
        self.command = command
        self.button = button
        self.callback = get_callable(command)
        # Inspect callback parameters
        self.parameters = {}
        sig = inspect.signature(callable)
        for parameter in sig.parameters.values():
            self.parameters[parameter.name] = parameter.annotation

    def __create_kwargs(self, message: Message) -> dict:
        kwargs = {}
        for name, dtype in self.parameters.items():
            if dtype == Message:
                kwargs[name] = message
            elif dtype == Button:
                kwargs[name] = self.button
        return kwargs

    def __call__(self, message: Message) -> Result:
        try:
            return self.callback(**self.__create_kwargs(message=message))
        except Exception as e:
            logger.error("Error running callback: %s", e)
            return Result()


class Button:
    State = ButtonState

    def __init__(
        self,
        led_on: partial,
        action: Message.Action,
        n: int,
        command: str,
        color_on: RGB,
        color_off: RGB = RGB(),  # black / turned off
        color_err: RGB = RGB(r=255),  # red
        initial_state: ButtonState = ButtonState.off,
        state_func: Optional[str] = None,
    ):
        """Create a button.

        Args:
            led_on: Function for turning the led on.
            action: Type of action that this button should respond to.
            n: Button number.
            command: String path to the callback.
            color_on: Button on color.
            color_off: Button off color.
            color_err: Button error color.
            initial_state: Initial button state.
            state_func: String path to the callable that will return the
                initial button state.
        """
        self.action = action
        self.n = n
        self.command = command
        self.state_func = (
            None if state_func is None else get_callable(state_func)
        )
        self.state = (
            initial_state if self.state_func is None else self.state_func()
        )
        self.color_on = color_on
        self.color_off = color_off
        self.color_err = color_err
        self._led_on = led_on
        self.callback = Callback(command=command, button=self)

    @classmethod
    def from_dict(cls, led_on: partial, d: dict) -> "Button":
        color_err = RGB.parse(d.get("color_err", "#FF0000"))
        initial_state = ButtonState(
            d.get("initial_state", ButtonState.off.value)
        )
        state_func = d.get("state_func", None)

        button = cls(
            led_on=led_on,
            action=Message.Action(d.get("action", Message.Action.click)),
            n=d["n"],
            command=d["command"],
            color_on=RGB.parse(d["color_on"]),
            color_off=RGB.parse(d["color_off"]),
            color_err=color_err,
            initial_state=initial_state,
            state_func=state_func,
        )

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

    def execute(self, message: Message) -> Result:
        return self.callback(message=message)


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

        self.launchpad.input.set_callback(Message.Action.click, self.callback)
        self.launchpad.input.set_callback(Message.Action.press, self.callback)
        self.launchpad.input.set_callback(
            Message.Action.release, self.callback
        )

    def reset(self, other_led_off=True):
        if other_led_off:
            # Reset all leds
            self.launchpad.led_all_off()

        # Put all buttons in the off state
        for button in self.layout.values():
            button.led_on()

    def callback(self, message: Message):
        try:
            button = self.layout.get(message.n, None)
            if button is not None and button.action == message.action:
                result = button.execute(message=message)
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
            logger.error(
                "Failed to execute button: %s. Error: %s", message.n, e
            )
