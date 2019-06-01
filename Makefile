# Install `curseradio-improved' locally.
.PHONY: all test clean

all:
	flake8 curseradio_improved/curseradio_improved.py
	sudo pip3 install -e .
	sudo python3 setup.py sdist bdist_wheel

test:
	curseradio-improved

clean:
	sudo rm -rf curseradio_improved.egg-info build/ dist/ $(shell which curseradio-improved)
