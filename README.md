# Curseradio-Improved
[![PyPI](https://img.shields.io/pypi/v/curseradio-improved.svg)](https://pypi.org/project/curseradio-improved/)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/curseradio-improved.svg)

## Overview
> An internet radio in the terminal.

![Screenshot](./assets/curseradio-improved.png)

`Curseradio-improved` is an improved version of [`curseradio`](https://github.com/chronitis/curseradio), a `curses` interface for browsing and playing an `OPML` directory of internet radio streams. It is designed to use the *tunein* directory found [here](http://opml.radiotime.com/), but could be adapted to others.

Audio playback uses [mpv](http://mpv.io/). `Curseradio-improved` requires `python3` and the libraries `requests`, `xdg` and `lxml`.

## Installation
Install the module from `PyPI`:
```bash
pip3 install curseradio-improved
curseradio-improved # tests the success installation
```

You can also install `curseradio-improved` from source by cloning (or downloading the code from) this repository. Then type:
```bash
make # might prompt for `sudo' password
curseradio-improved # tests the success installation
```

## Settings
Settings are parsed from a `configs.json`. Currently, colors and key bindings can be change to your liking. Additional settings like status bar display text, section separators and more will be configurable in the future. To find the location of the settings file of your installation, type:

```bash
echo "$(pip3 show curseradio-improved | grep -i 'location' | awk '{ print $2 }')/curseradio_improved/configs.json"
```

## Key Bindings
You can use the keys below to navigate and select things in the `tui`. `vi`-like keys should work intuitively.

Key(s)                                                           |                         Command
-----------------------------------------------------------------|--------------------------------
<kbd>↑</kbd> or <kbd>k</kbd>, <kbd>↓</kbd> or <kbd>j</kbd>       |                        navigate
<kbd>PgUp</kbd> or <kbd>p</kbd>, <kbd>PgDn</kbd> or <kbd>n</kbd> |     navigate inbetween sections
<kbd>Home</kbd> or <kbd>g</kbd>, <kbd>End</kbd> or <kbd>G</kbd>  |                   to top/bottom
<kbd>Enter</kbd>                                                 | open/close folders, play stream
<kbd>s</kbd>                                                     |             stop playing stream
<kbd>q</kbd>                                                     |                            quit
<kbd>f</kbd>                                                     |                toggle favourite

## License
`curseradio-improved` is MIT-licensed (see [LICENSE.md](./LICENSE.md)).
