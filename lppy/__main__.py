import sys
import argparse

from lppy.layout import Layout
from lppy.server import Server
from lppy.models import LaunchpadMiniMk3


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("layout", type=str)
    return parser


def cli():
    parser = create_parser()
    ns = parser.parse_args(sys.argv[1:])

    launchpad = LaunchpadMiniMk3()
    layout = Layout(path=ns.layout, launchpad=launchpad)

    server = Server(layout=layout)
    server.run()


if __name__ == "__main__":
    cli()
