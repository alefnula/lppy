# Python library for controlling Novation Launchpads.

Tested on Launchpad Mini Mk3 device.

## Install

```
pip install -U lppy
```

## Usage

Look at the examples in the the [examples](https://github.com/alefnula/lppy/tree/master/examples)
folder.

* Use the Launchpad like a Piano
* Show 8x8 rgb images
* Get the firmware version
* Create a fake Launchpad MIDI ports


## Attributions

This library is based on the [launchpad.py](https://github.com/FMMT666/launchpad.py)
library and [novation-launchpad](https://github.com/eavelardev/novation-launchpad).

It is PEP8 compliant and among other differences it uses
[python-rtmidi](https://pypi.org/project/rtmidi-python/) instead of ``pygame``
and uses callback function instead of polling for reading data.
