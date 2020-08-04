import time
import random

from lppy.launchpad_mini_mk3 import LaunchpadMiniMk3


def main():
    # create an instance
    lp = LaunchpadMiniMk3()
    lp.open()

    # Clear the buffer because the Launchpad remembers everything :-)
    lp.button_flush()

    buton_hit = 10

    while 1:
        lp.led_control_raw(
            random.randint(0, 127),
            random.randint(0, 63),
            random.randint(0, 63),
            random.randint(0, 63),
        )

        time.sleep(0.001 * 5)

        but = lp.button_state_raw()

        if but != []:
            buton_hit -= 1
            if buton_hit < 1:
                break
            print(buton_hit, " event: ", but)

    # turn all LEDs off
    lp.reset()

    # close the Launchpad (will quit with an error due to a PyGame bug)
    lp.close()


if __name__ == "__main__":
    main()
