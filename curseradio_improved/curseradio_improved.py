#!/bin/python3
"""
Curses application for navigating and playing radio streams (using the
tunein directory at http://opml.radiotime.com/).

Uses `mpv' to play streams. Works for any stream which works when invoked
as `$mpv <stream-location>'.

A favourites file (also stored as OPML) is written to
`$XDG_DATA_HOME/curseradio_improved/favourites.opml'.
"""
import curses
import json
import pathlib
import subprocess
from os import path

import lxml.etree
import requests
import xdg.BaseDirectory


class OPMLNode:
    """
    Represents an OPML <outline> element. Only instantiate subclasses.
    """
    @classmethod
    def from_xml(cls, url, text="", attr=None):
        """
        Load an OPML XML file. Returns a fake parent OPMLOutline node with
        children set to all the outlines contained in the file. (The header
        is currently discarded).
        """
        if attr is None:
            attr = {}
        tree = lxml.etree.parse(url)
        result = cls(text=text, attr=attr)
        result.children = [OPMLNode.from_element(o)
                           for o in tree.xpath("/opml/body/outline")]
        return result

    @classmethod
    def from_element(cls, element):
        """
        Converts a single <outline> node into the appropriate OPMLOutline
        subclass depending on attributes. Currently detects only plain
        outlines (simple folders), links (deferred folders) and audio leaf
        elements.

        TODO: Support other leaf element types.
        """
        text = element.get("text")
        attr = dict(element.attrib)
        type = attr.get("type", None)
        if type is None and len(element) > 0:
            type = "outline"

        if type == "outline":
            node = OPMLOutline(text=text, attr=attr)
            for child in element.xpath("./outline"):
                node.children.append(cls.from_element(child))
        elif type == "link":
            node = OPMLOutlineLink(text=text, attr=attr)
            assert len(element) == 0
        elif type == "audio":
            node = OPMLAudio(text=text, attr=attr)
            assert len(element) == 0
        return node

    def __init__(self, text, attr):
        self.text = text
        self.attr = attr

    def render(self, depth):
        """
        Return a 4-tuple of text to display (text truncated if too long)
         * main title (~50% width)
         * subtext (~40% width)
         * data0 (4 chars)
         * data1 (5 chars)
        """
        raise NotImplementedError

    def activate(self):
        """
        Action when the item is selected and enter pressed. Yield either
        strings (progress messages) or a list (command list for popen).
        """
        raise NotImplementedError

    def flatten(self, result, depth=0):
        """
        Visitor method to return a flattened ordered list of (obj, depth)
        tuples in menu order, respecting current collapse settings.
        """
        result.append((self, depth))
        return result

    def to_element(self):
        """
        Return the object and its children as an <outline> element.
        """
        return lxml.etree.Element("outline", attrib=self.attr)

    def to_xml(self):
        """
        Return the element wrapped in an <opml> toplevel element.
        """
        opml = lxml.etree.Element("opml")
        body = lxml.etree.SubElement(opml, "body")
        body.append(self.to_element())
        return opml


class OPMLAudio(OPMLNode):
    """
    Audio leaf node (<outline> with type=audio). URL attribute is expected to
    return a list of playlist URLs when accessed which can be passed to a
    player command. `bitrate`, `reliability`, `current_track` and `subtext`
    attributes are considered.
    """

    def __init__(self, text, attr):
        self.text = text
        self.attr = attr
        self.url = attr["URL"]
        self.bitrate = int(attr.get("bitrate", 0))
        self.reliability = int(attr.get("reliability", 0))
        self.formats = attr.get("formats", "")
        self.leaf = True
        if "current_track" in attr:
            self.secondary = attr["current_track"]
        elif "subtext" in attr:
            self.secondary = attr["subtext"]
        else:
            self.secondary = ""

    def activate(self):
        yield "Fetching playlist"
        r = requests.get(self.url)
        playlist = r.text.split('\n')[0]
        yield [playlist]

    def render(self, open_delim, close_delim):
        """
        Called for every audio leave node on drawing. `open_delim' and
        `close_delim' are not used.
        """
        return (self.text, self.secondary,
                "{}k".format(self.bitrate), '|'*(self.reliability//20))


class OPMLOutline(OPMLNode):
    """
    Simple branch-level element, filled from the host file at creation time.
    """

    def __init__(self, text, attr):
        self.text = text
        self.attr = attr
        self.children = []
        self.collapsed = True
        self.leaf = False

    def activate(self):
        self.collapsed = not self.collapsed
        yield from ()

    def flatten(self, result, depth=0):
        result.append((self, depth))
        if not self.collapsed:
            for c in self.children:
                c.flatten(result, depth+1)
        return result

    def render(self, open_delim, close_delim):
        """
        Render display text, respecting the edge case of the tree root.
        """
        if self.text != "":
            return ("{} {}".format(
                open_delim if self.collapsed else close_delim, self.text
            ), "", "", "")
        else:
            return ("{}".format(open_delim if self.collapsed else close_delim),
                    "", "", "")

    def to_element(self):
        elem = super().to_element()
        for c in self.children:
            elem.append(c.to_element())
        return elem


class OPMLOutlineLink(OPMLOutline):
    """
    Branch level node with type=link. Upon activation, the URL is fetched,
    parsed as OPML and all top-level outlines added as children of this node.
    """

    def __init__(self, text, attr):
        super().__init__(text, attr)
        self.url = attr["URL"]
        self.ready = False

    def activate(self):
        if not self.ready:
            yield "Loading {}".format(self.url)
            fakeroot = OPMLOutline.from_xml(self.url)
            self.children = fakeroot.children
            self.ready = True
            yield "Loading... done"
        self.collapsed = not self.collapsed


class OPMLFavourites(OPMLOutline):
    """
    A special outline subclass representing a locally stored favourites list
    which tracks whether it has been altered so it can be saved if necessary.
    """

    def __init__(self, text, attr):
        super().__init__("Favourites", {})
        self.dirty = False

    def toggle(self, other):
        self.dirty = True
        if other in self.children:
            self.children.remove(other)
        else:
            self.children.append(other)

    def to_xml(self):
        """
        For the favourites object, we skip generating an extra <outline>
        (corresponding to this object), and just place the children (ie,
        the actual favourite items) as the toplevel.
        """
        opml = lxml.etree.Element("opml")
        body = lxml.etree.SubElement(opml, "body")
        for c in self.children:
            body.append(c.to_element())
        return opml


class OPMLBrowser:
    """
    Curses browser for an OPML tree. Includes simple keyboard navigation
    and launching child commands based on OPML leaf nodes.
    """

    def __init__(self, screen):
        """
        This is intended to be invoked using curses.wrapper. The first
        argument is the curses window and the second the OPML root URL.
        """
        self.config = self.load_config()
        self.keymap = self.get_keymap()
        self.root = OPMLOutline.from_xml(self.config['opml']['root'])
        self.root.collapsed = False
        self.favourites = self.load_favourites()
        self.root.children.insert(0, self.favourites)
        self.screen = screen
        self.selected = self.root
        self.cursor = 0
        self.top = 0
        self.flat = self.root.flatten([])
        self.maxy, self.maxx = self.screen.getmaxyx()
        self.child = None
        self.status = ""

        # UI settings
        self.xmargin = 1
        self.ymargin = 1
        self.status_xmargin = 3
        self.status_ymargin = 3

        # prevent custom color schemes (e.g. in Gnome term) from messing up the
        # background color
        curses.use_default_colors()

        curses.curs_set(0)  # hide cursor
        self.init_colors()  # initialize colors
        self.display()  # display starting screen
        self.interact()  # main loop

    def load_favourites(self):
        for p in xdg.BaseDirectory.load_data_paths("curseradio_improved"):
            opmlpath = pathlib.Path(p, "favourites.opml")
            if opmlpath.exists():
                return OPMLFavourites.from_xml(str(opmlpath))
        return OPMLFavourites("", {})

    def save_favourites(self):
        path = xdg.BaseDirectory.save_data_path("curseradio_improved")
        if self.favourites.dirty:
            opmlpath = pathlib.Path(path, "favourites.opml")
            opml = lxml.etree.ElementTree(self.favourites.to_xml())
            opml.write(str(opmlpath))

    def load_config(self, name="configs.json"):
        """
        Load configuration from `json' file.
        """
        with open(path.join(path.dirname(__file__), name)) as f:
            return json.loads(f.read())

    def get_keymap(self):
        """
        Get key mappings from configs.
        """
        keymap = {}

        for key in (
                "up", "up_vi", "down", "down_vi", "start", "start_vi", "end",
                "end_vi", "pageup", "pageup_vi", "pagedown", "pagedown_vi",
                "enter", "stop", "exit", "favourite"
        ):
            value = self.config["keymap"][key]
            if value.startswith("KEY_"):
                keymap[key] = getattr(curses, value)
            else:
                keymap[key] = ord(value)
        return keymap

    def init_colors(self):
        """
        Initialize curses colors.
        """
        self.colors = {}
        for i in range(curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        self.colors["white"] = curses.color_pair(0)
        self.colors["black"] = curses.color_pair(1)
        self.colors["red"] = curses.color_pair(2)
        self.colors["green"] = curses.color_pair(3)
        self.colors["yellow"] = curses.color_pair(4)
        self.colors["blue"] = curses.color_pair(5)
        self.colors["margenta"] = curses.color_pair(6)
        self.colors["cyan"] = curses.color_pair(7)

        # background colors
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(13, curses.COLOR_BLACK, curses.COLOR_BLUE)
        curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
        self.colors["inverted"] = curses.color_pair(8)
        self.colors["green-bg"] = curses.color_pair(9)
        self.colors["red-bg"] = curses.color_pair(10)
        self.colors["cyan-bg"] = curses.color_pair(11)
        self.colors["yellow-bg"] = curses.color_pair(12)
        self.colors["blue-bg"] = curses.color_pair(13)
        self.colors["margenta-bg"] = curses.color_pair(14)

    def draw_outline(self):
        """
        Draw an outline around the UI.
        """
        color = self.colors[self.config["outline-color"]]
        self.screen.addstr(0, 0, "┌", color)
        self.screen.addstr(0, self.maxx-1, "┐", color)
        self.screen.addstr(self.maxy-2, self.maxx-1, "┘", color)
        self.screen.addstr(self.maxy-2, 0, "└", color)
        for i in range(1, self.maxx-1):
            self.screen.addstr(0, i, "─", color)
            self.screen.addstr(self.maxy-2, i, "─", color)
        for i in range(1, self.maxy-2):
            self.screen.addstr(i, 0, "│", color)
            self.screen.addstr(i, self.maxx-1, "│", color)

        # draw title
        title = " Curseradio - Improved "
        self.screen.addstr(0, self.maxx//2-len(title)//2, title,
                           self.colors[self.config["title-color"]])

    def display(self, msg=None):
        """
        Redraw the screen, possibly showing a message or the status bar.
        """
        self.screen.clear()

        width0 = 6*(self.maxx - 10)//10
        width1 = 4*(self.maxx - 10)//10

        # the color of a selected item, message and the status bar
        selected_style = self.colors[self.config["colors"]["selected-item"]]
        msg_style = self.colors[self.config["colors"]["message"]]
        status_style = self.colors[self.config["colors"]["statusbar"]]

        self.draw_outline()

        showobjs = self.flat[self.top:self.top+self.maxy-self.status_ymargin-2]
        for i, (obj, depth) in enumerate(showobjs):
            text = obj.render(
                self.config["opened_delimiter"],
                self.config["closed_delimiter"]
            )
            style = selected_style if i == self.cursor else curses.A_NORMAL
            self.screen.addstr(i+self.ymargin, depth*2+self.xmargin,
                               text[0][:width0-depth*2], style)
            self.screen.addstr(i+self.ymargin, width0+2, text[1][:width1-4])
            self.screen.addstr(i+self.ymargin, width0+width1, text[2][:4])
            self.screen.addstr(i+self.ymargin, width0+width1+5, text[3][:5])

        if msg is not None:
            self.screen.addstr(self.maxy-self.status_ymargin,
                               0+self.status_xmargin,
                               msg[:self.maxx-1], msg_style)
        else:
            self.screen.addstr(self.maxy-self.status_ymargin,
                               0+self.status_xmargin,
                               self.status[:self.maxx-1], status_style)

        self.screen.refresh()
        curses.doupdate()

    def move(self, rel=None, to=None):
        """
        Recalculate screen scrolling after movement.
        """
        # determine where to go to
        if to is not None:
            if to == "start":
                target = 0
            elif to == "end":
                target = len(self.flat) - 1
        elif rel is not None:
            target = self.top + self.cursor + rel

        # check bounds of `target'
        target = min(target, len(self.flat)-1)
        target = max(target, 0)
        self.selected = self.flat[target][0]

        # reached upper bound
        if target < self.top:
            self.top = target
            self.cursor = 0
        # reached lower bound
        elif target > self.top + self.maxy - 3 - self.status_ymargin:
            self.top = target - (self.maxy - 3 - self.status_ymargin)
            self.cursor = self.maxy - 3 - self.status_ymargin
        # moving within bounds
        else:
            self.cursor = target - self.top

    def interact(self):
        """
        Main loop. Listen for keyboard input and respond.
        """
        while True:
            ch = self.screen.getch()
            if ch == curses.KEY_RESIZE:
                self.maxy, self.maxx = self.screen.getmaxyx()
            elif ch == self.keymap["up"] or ch == self.keymap["up_vi"]:
                self.move(rel=-1)
            elif ch == self.keymap["down"] or ch == self.keymap["down_vi"]:
                self.move(rel=1)
            elif ch == self.keymap["start"] or ch == self.keymap["start_vi"]:
                self.move(to="start")
            elif ch == self.keymap["end"] or ch == self.keymap["end_vi"]:
                self.move(to="end")
            elif ch == self.keymap["pageup"] or ch == self.keymap["pageup_vi"]:
                self.move(rel=-self.maxy)
            elif ch == self.keymap["pagedown"] or ch == self.keymap[
                "pagedown_vi"
            ]:
                self.move(rel=self.maxy)
            elif ch == self.keymap["enter"] or ch == ord('\n'):
                for msg in self.selected.activate():
                    if isinstance(msg, str):
                        self.display(msg=msg)
                    elif isinstance(msg, list):  # command to run
                        if self.child is not None:
                            self.child.terminate()
                            self.child.wait()

                        command = [self.config['playback']['command']] + msg
                        self.child = subprocess.Popen(
                            command, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
                        )
                        self.status = self.config["statusbar-text"].format(
                            self.selected.text)

                self.flat = self.root.flatten([])
                self.move(rel=0)
            elif ch == self.keymap["exit"]:
                if self.child is not None:
                    self.child.terminate()
                    self.child.wait()
                self.save_favourites()
                return
            elif ch == self.keymap["stop"]:
                if self.child is not None:
                    self.child.terminate()
                    self.child.wait()
            elif ch == self.keymap["favourite"]:
                self.favourites.toggle(self.selected)
                self.flat = self.root.flatten([])
                self.move(rel=0)

            if self.child is not None:
                if self.child.poll() is not None:
                    self.child = None
                    self.status = ""

            self.display()  # render the new screen
