import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from lppy.enums import RGB, ButtonState, Scroll
from lppy.models.launchpad import LaunchpadBase


@dataclass
class Button:
    lp: LaunchpadBase
    id: int
    action: str
    state: ButtonState
    color_on: RGB
    color_off: RGB
    color_err: RGB = RGB(r=255)

    @classmethod
    def from_dict(cls, lp: LaunchpadBase, d: dict) -> "Button":
        button = cls(
            lp=lp,
            id=d["id"],
            action=d["action"],
            state=ButtonState.off,
            color_on=RGB.parse(d["color_on"]),
            color_off=RGB.parse(d["color_off"]),
        )
        if "color_err" in d:
            button.color_err = RGB.parse(d["color_err"])
        return button

    def light_on(self):
        if self.state == ButtonState.on:
            self.lp.led_on(self.color_on, n=self.id)
        elif self.state == ButtonState.off:
            self.lp.led_on(self.color_off, n=self.id)
        elif self.state == ButtonState.err:
            self.lp.led_on(self.color_off, n=self.id)

    def light_off(self):
        self.lp.led_on(RGB())

    def set_state(self, state: ButtonState):
        self.state = state
        self.light_on()


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
    RUN_SCRIPT = (
        "import importlib; "
        "module = importlib.import_module('{module}'); "
        "function = getattr(module, '{function}'); "
        "function()"
    )

    def __init__(self, path: str, launchpad: LaunchpadBase):
        """Initialize layout from json file.

        Args:
            path (str): Path to the layout json file.
            launchpad (LaunchpadBase): Instance of a launchpad.
        """
        self.path = Path(path)
        self.launchpad = launchpad

        data = json.loads(self.path.read_text(encoding="utf-8"))

        self.python = data["python"]

        python_path = self.path.parent.absolute()
        old_python_path = os.environ.get("PYTHONPATH", "").strip()
        if old_python_path:
            self.python_path = f"{python_path}:{old_python_path}"
        else:
            self.python_path = python_path

        # Load layout
        self.layout = {}
        for button_data in data["layout"]:
            button = Button.from_dict(lp=self.launchpad, d=button_data)
            self.layout[button.id] = button

        self.reset_buttons()

        self.launchpad.input.set_callback(self.callback)

    def reset_buttons(self):
        # Reset all leds
        self.launchpad.led_all_on()

        # Put all buttons in the off state
        for button in self.layout.values():
            button.light_on()

    def execute(self, button: Button):
        module, function = button.action.split(":")
        output = subprocess.check_output(
            [
                self.python,
                "-c",
                self.RUN_SCRIPT.format(module=module, function=function),
            ],
            env={"PYTHONPATH": self.python_path},
        )
        result = Result.from_dict(json.loads(output))
        if result.text is not None:
            self.launchpad.write_string(
                string=result.text,
                color=result.text_color,
                scroll=result.scroll,
            )
            self.reset_buttons()
        button.set_state(result.state)

    def callback(self, msg):
        if msg[0][0] == 144 and msg[0][2] == 127:
            button_no = msg[0][1]
            if button_no == 19:
                self.reset_buttons()
            else:
                button = self.layout.get(button_no, None)
                if button is not None:
                    self.execute(button=button)
