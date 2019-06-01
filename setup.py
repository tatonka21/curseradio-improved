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


def readme():
    """
    Import README.md as a long package description.
    """
    with open(
            os.path.join(os.path.dirname(__file__),
                         "README.md"), encoding="utf-8"
    ) as f:
        return f.read()


setup(
    name="curseradio-improved",
    version=__version__,
    description=description,
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    author="Daniel Schuette",
    author_email="d.schuette@online.de",
    url="https://github.com/DanielSchuette/curseradio-improved",
    packages=["curseradio_improved"],
    license="MIT",
    requires=["lxml", "requests", "xdg"],
    entry_points={
        "console_scripts":
        "curseradio-improved = curseradio_improved.__main__:main"
    }
)
