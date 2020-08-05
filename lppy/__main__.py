import io
import sys
import json
import time
import argparse
import subprocess

import lppy


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("layout", type=str)
    return parser


class Server:
    def __init__(self, lp: lppy.LaunchpadMiniMk3, layout: dict):
        self.lp = lp

        self.registry = {}
        for item in layout:
            button = item["button"]
            color = lppy.RGB(**item["color"])
            lp.led_on(color=color, n=button)
            self.registry[item["button"]] = {
                "action": item["action"],
                "examples": item["examples"],
            }
        self.lp.input.set_callback(self.callback)

    def callback(self, msg):
        if msg[0][0] == 144 and msg[0][2] == 127:
            button = msg[0][1]
            if button in self.registry:
                action = self.registry[button]["action"]
                data = self.registry[button]["examples"]

                if action == "script":
                    exec(data)
                elif action == "command":
                    subprocess.call(data)

    def run(self):
        while True:
            try:
                time.sleep(100)
            except KeyboardInterrupt:
                return


def cli(args):
    parser = create_parser()
    ns = parser.parse_args(args)
    with io.open(ns.layout, "r") as f:
        layout = json.loads(f.read())

    lp = lppy.LaunchpadMiniMk3()
    server = Server(lp=lp, layout=layout)

    server.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
