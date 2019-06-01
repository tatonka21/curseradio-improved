# Curseradio-Improved

## Overview
> An internet radio in the terminal.

`Curseradio-improved` is an improved version of [`curseradio`](), a `curses` interface for browsing and playing an `OPML` directory of internet radio streams. It is designed to use the *tunein* directory found [here](http://opml.radiotime.com/), but could be adapted to others.

Audio playback uses [`mpv`](http://mpv.io/). Curseradio requires `python3` and the libraries `requests`, `xdg` and `lxml`.

## Installation
Install the `curseradio-improved` by downloading the source code (or cloning this repository) and typing:
```bash
make # might prompt for `sudo' password
make test # tests the success installation
```

## Key Bindings
Key(s)                           |                         Command
---------------------------------|--------------------------------
<kbd>↑</kbd>, <kbd>↓</kbd>       |                        navigate
<kbd>PgUp</kbd>, <kbd>PgDn</kbd> |                navigate quickly
<kbd>Home</kbd>, <kbd>End</kbd>  |                   to top/bottom
<kbd>Enter</kbd>                 | open/close folders, play stream
<kbd>k</kbd>                     |             stop playing stream
<kbd>q</kbd>                     |                            quit
<kbd>f</kbd>                     |                toggle favourite

## License
`Curseradio-improved` is MIT-licensed (see [LICENSE.md](./LICENSE.md)).
