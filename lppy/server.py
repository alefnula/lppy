import time

from lppy.layout import Layout


class Server:
    def __init__(self, layout: Layout):
        self.layout = layout

    def run(self):
        while True:
            try:
                time.sleep(100)
            except KeyboardInterrupt:
                return
