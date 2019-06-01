#!/bin/python3
import curses

from .curseradio_improved import OPMLBrowser


def main():
    curses.wrapper(OPMLBrowser)


if __name__ == '__main__':
    main()
