#!/usr/bin/env python3
import os

from setuptools import setup

__version__ = None
description = "An improved Curses interface for listening to internet radio."

with open(
        os.path.join(os.path.dirname(__file__),
                     "curseradio_improved", "__init__.py")
) as f:
    for line in f.readlines():
        if line.startswith("__version__"):
            exec(line)

setup(
    name="curseradio-improved",
    version=__version__,
    description=description,
    author="Gordon Ball, Daniel Schuette",
    author_email="gordon@chronitis.net, d.schuette@online.de",
    url="https://github.com/DanielSchuette/curseradio-improved",
    packages=["curseradio_improved"],
    license="MIT",
    requires=["lxml", "requests", "pyxdg"],
    entry_points={
        "console_scripts":
        "curseradio-improved = curseradio_improved.__main__:main"
    }
)
